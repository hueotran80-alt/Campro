using CamPro.Web.Models;
using Microsoft.AspNetCore.Identity;
using MySqlConnector;

namespace CamPro.Web.Data;

public sealed class StoreRepository(MySqlConnectionFactory factory)
{
    public async Task<StoreState> GetStateAsync(long? userId, CancellationToken ct)
    {
        await using var cn = factory.Create();
        await cn.OpenAsync(ct);
        var products = await ReadProductsAsync(cn, ct);
        var categories = await ReadCategoriesAsync(cn, ct);
        var suppliers = await ReadSuppliersAsync(cn, ct);
        var customers = await ReadCustomersAsync(cn, ct);
        var orders = await ReadOrdersAsync(cn, ct);
        var coupons = await ReadCouponsAsync(cn, ct);
        var articles = await ReadArticlesAsync(cn, ct);
        var contacts = await ReadContactsAsync(cn, ct);
        var cart = userId is null ? [] : await ReadCartAsync(cn, userId.Value, ct);
        var session = userId is null ? null : customers.FirstOrDefault(x => x.Id == userId.Value)
            ?? await FindUserDtoAsync(cn, userId.Value, ct);
        return new StoreState
        {
            Products = products, Categories = categories, Suppliers = suppliers,
            Customers = customers, Orders = orders, Coupons = coupons,
            Articles = articles, Contacts = contacts, Cart = cart,
            Session = session, Compare = []
        };
    }

    public async Task SyncAsync(StoreState state, long? userId, CancellationToken ct)
    {
        ValidateState(state);
        await using var cn = factory.Create();
        await cn.OpenAsync(ct);
        await using var tx = await cn.BeginTransactionAsync(ct);
        try
        {
            foreach (var x in state.Categories)
                await ExecuteAsync(cn, tx, "INSERT INTO categories(id,name,description,active) VALUES(@id,@name,@description,@active) ON DUPLICATE KEY UPDATE name=VALUES(name),description=VALUES(description),active=VALUES(active)", ct,
                    ("@id",x.Id),("@name",x.Name),("@description",x.Description),("@active",x.Active));
            foreach (var x in state.Suppliers)
                await ExecuteAsync(cn, tx, "INSERT INTO suppliers(id,name,description,email,phone,active) VALUES(@id,@name,@description,@email,@phone,@active) ON DUPLICATE KEY UPDATE name=VALUES(name),description=VALUES(description),email=VALUES(email),phone=VALUES(phone),active=VALUES(active)", ct,
                    ("@id",x.Id),("@name",x.Name),("@description",x.Description),("@email",x.Email),("@phone",x.Phone),("@active",x.Active));
            foreach (var x in state.Products)
                await ExecuteAsync(cn, tx, "INSERT INTO products(id,name,subtitle,brand,category,resolution,connection_type,price,old_price,stock,image,tag,angle,night_mode,active,description) VALUES(@id,@name,@subtitle,@brand,@category,@resolution,@connection,@price,@oldPrice,@stock,@image,@tag,@angle,@night,@active,@description) ON DUPLICATE KEY UPDATE name=VALUES(name),subtitle=VALUES(subtitle),brand=VALUES(brand),category=VALUES(category),resolution=VALUES(resolution),connection_type=VALUES(connection_type),price=VALUES(price),old_price=VALUES(old_price),stock=VALUES(stock),image=VALUES(image),tag=VALUES(tag),angle=VALUES(angle),night_mode=VALUES(night_mode),active=VALUES(active),description=VALUES(description)", ct,
                    ("@id",x.Id),("@name",x.Name),("@subtitle",x.Subtitle),("@brand",x.Brand),("@category",x.Category),("@resolution",x.Resolution),("@connection",x.Connection),("@price",x.Price),("@oldPrice",x.OldPrice),("@stock",x.Stock),("@image",x.Image),("@tag",x.Tag),("@angle",x.Angle),("@night",x.Night),("@active",x.Active),("@description",x.Description));
            foreach (var x in state.Coupons)
                await ExecuteAsync(cn, tx, "INSERT INTO coupons(id,code,discount_type,discount_value,min_amount,max_amount,active) VALUES(@id,@code,@type,@value,@min,@max,@active) ON DUPLICATE KEY UPDATE code=VALUES(code),discount_type=VALUES(discount_type),discount_value=VALUES(discount_value),min_amount=VALUES(min_amount),max_amount=VALUES(max_amount),active=VALUES(active)", ct,
                    ("@id",x.Id),("@code",x.Code.ToUpperInvariant()),("@type",x.Type),("@value",x.Value),("@min",x.Min),("@max",x.Max),("@active",x.Active));
            foreach (var x in state.Articles)
                await ExecuteAsync(cn, tx, "INSERT INTO articles(id,title,category,image,published,body) VALUES(@id,@title,@category,@image,@published,@body) ON DUPLICATE KEY UPDATE title=VALUES(title),category=VALUES(category),image=VALUES(image),published=VALUES(published),body=VALUES(body)", ct,
                    ("@id",x.Id),("@title",x.Title),("@category",x.Category),("@image",x.Image),("@published",x.Published),("@body",x.Body));
            foreach (var x in state.Contacts)
                await ExecuteAsync(cn, tx, "INSERT INTO contacts(id,name,email,phone,subject,message,status,reply) VALUES(@id,@name,@email,@phone,@subject,@message,@status,@reply) ON DUPLICATE KEY UPDATE name=VALUES(name),email=VALUES(email),phone=VALUES(phone),subject=VALUES(subject),message=VALUES(message),status=VALUES(status),reply=VALUES(reply)", ct,
                    ("@id",x.Id),("@name",x.Name),("@email",x.Email),("@phone",x.Phone),("@subject",x.Subject),("@message",x.Message),("@status",x.Status),("@reply",x.Reply));
            foreach (var x in state.Customers)
                await UpsertCustomerAsync(cn, tx, x, ct);
            foreach (var order in state.Orders)
            {
                var date = DateOnly.TryParse(order.Date, out var parsed) ? parsed : DateOnly.FromDateTime(DateTime.Today);
                await ExecuteAsync(cn, tx, "INSERT INTO orders(id,customer,email,shipping_email,phone,address,note,order_date,total,discount,status,payment,paid,demo) VALUES(@id,@customer,@email,@shippingEmail,@phone,@address,@note,@date,@total,@discount,@status,@payment,@paid,@demo) ON DUPLICATE KEY UPDATE customer=VALUES(customer),email=VALUES(email),shipping_email=VALUES(shipping_email),phone=VALUES(phone),address=VALUES(address),note=VALUES(note),order_date=VALUES(order_date),total=VALUES(total),discount=VALUES(discount),status=VALUES(status),payment=VALUES(payment),paid=VALUES(paid),demo=VALUES(demo)", ct,
                    ("@id",order.Id),("@customer",order.Customer),("@email",order.Email),("@shippingEmail",order.ShippingEmail),("@phone",order.Phone),("@address",order.Address),("@note",order.Note),("@date",date.ToDateTime(TimeOnly.MinValue)),("@total",order.Total),("@discount",order.Discount),("@status",order.Status),("@payment",order.Payment),("@paid",order.Paid),("@demo",order.Demo));
                await ExecuteAsync(cn, tx, "DELETE FROM order_items WHERE order_id=@id", ct, ("@id",order.Id));
                foreach (var item in order.Items)
                    await ExecuteAsync(cn, tx, "INSERT INTO order_items(order_id,product_id,product_name,quantity,price,image) VALUES(@orderId,@productId,@name,@quantity,@price,@image)", ct,
                        ("@orderId",order.Id),("@productId",item.Id),("@name",item.Name),("@quantity",item.Quantity),("@price",item.Price),("@image",item.Image));
            }

            await DeleteMissingAsync(cn, tx, "products", state.Products.Select(x => x.Id), ct);
            await DeleteMissingAsync(cn, tx, "categories", state.Categories.Select(x => x.Id), ct);
            await DeleteMissingAsync(cn, tx, "suppliers", state.Suppliers.Select(x => x.Id), ct);
            await DeleteMissingAsync(cn, tx, "coupons", state.Coupons.Select(x => x.Id), ct);
            await DeleteMissingAsync(cn, tx, "articles", state.Articles.Select(x => x.Id), ct);
            await DeleteMissingAsync(cn, tx, "contacts", state.Contacts.Select(x => x.Id), ct);
            await DeleteMissingStringsAsync(cn, tx, "orders", state.Orders.Select(x => x.Id), ct);

            if (userId is not null)
            {
                await ExecuteAsync(cn, tx, "DELETE FROM carts WHERE user_id=@userId", ct, ("@userId",userId.Value));
                foreach (var item in state.Cart)
                    await ExecuteAsync(cn, tx, "INSERT INTO carts(user_id,product_id,quantity) VALUES(@userId,@productId,@quantity)", ct,
                        ("@userId",userId.Value),("@productId",item.Id),("@quantity",item.Quantity));
            }
            await tx.CommitAsync(ct);
        }
        catch
        {
            await tx.RollbackAsync(ct);
            throw;
        }
    }

    public async Task<CustomerDto?> LoginAsync(string email, string password, CancellationToken ct)
    {
        await using var cn = factory.Create(); await cn.OpenAsync(ct);
        await using var cmd = new MySqlCommand("SELECT id,name,email,password_hash,phone,address,role,active FROM users WHERE email=@email LIMIT 1",cn);
        cmd.Parameters.AddWithValue("@email",email.Trim().ToLowerInvariant());
        await using var r = await cmd.ExecuteReaderAsync(ct);
        if (!await r.ReadAsync(ct) || !r.GetBoolean("active")) return null;
        var hasher = new PasswordHasher<object>();
        if (hasher.VerifyHashedPassword(new object(),r.GetString("password_hash"),password)==PasswordVerificationResult.Failed) return null;
        return ReadCustomer(r);
    }

    public async Task<(CustomerDto? User, string? Error)> RegisterAsync(RegisterRequest request, CancellationToken ct)
    {
        var email=request.Email.Trim().ToLowerInvariant();
        if(string.IsNullOrWhiteSpace(request.Name)||!email.Contains('@')||request.Password.Length<6)
            return (null,"Thông tin đăng ký chưa hợp lệ hoặc mật khẩu dưới 6 ký tự.");
        await using var cn=factory.Create(); await cn.OpenAsync(ct);
        var id=DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        var hash=new PasswordHasher<object>().HashPassword(new object(),request.Password);
        try
        {
            await ExecuteAsync(cn,null,"INSERT INTO users(id,name,email,password_hash,role,active) VALUES(@id,@name,@email,@hash,'customer',1)",ct,("@id",id),("@name",request.Name.Trim()),("@email",email),("@hash",hash));
            return (new CustomerDto{Id=id,Name=request.Name.Trim(),Email=email,Active=true,Role="customer"},null);
        }
        catch(MySqlException ex) when(ex.Number==1062){return(null,"Email đã được đăng ký.");}
    }

    public async Task<bool> ChangePasswordAsync(long userId,string current,string next,CancellationToken ct)
    {
        if(next.Length<6)return false;
        await using var cn=factory.Create();await cn.OpenAsync(ct);
        await using var get=new MySqlCommand("SELECT password_hash FROM users WHERE id=@id",cn);get.Parameters.AddWithValue("@id",userId);
        var old=(string?)await get.ExecuteScalarAsync(ct); if(old is null)return false;
        var hasher=new PasswordHasher<object>();
        if(hasher.VerifyHashedPassword(new object(),old,current)==PasswordVerificationResult.Failed)return false;
        var hash=hasher.HashPassword(new object(),next);
        await ExecuteAsync(cn,null,"UPDATE users SET password_hash=@hash WHERE id=@id",ct,("@hash",hash),("@id",userId));return true;
    }

    public async Task<bool> PingAsync(CancellationToken ct){await using var cn=factory.Create();await cn.OpenAsync(ct);await using var cmd=new MySqlCommand("SELECT 1",cn);return Convert.ToInt32(await cmd.ExecuteScalarAsync(ct))==1;}

    private static void ValidateState(StoreState s)
    {
        if(s.Products.Count>1000||s.Orders.Count>10000||s.Customers.Count>10000)throw new ArgumentException("Dữ liệu đồng bộ vượt giới hạn.");
        if(s.Products.Any(x=>x.Id<=0||string.IsNullOrWhiteSpace(x.Name)||x.Price<=0||x.Stock<0))throw new ArgumentException("Sản phẩm không hợp lệ.");
        if(s.Orders.Any(x=>string.IsNullOrWhiteSpace(x.Id)||x.Total<0||x.Items.Any(i=>i.Quantity<=0||i.Price<0)))throw new ArgumentException("Đơn hàng không hợp lệ.");
    }

    private static async Task UpsertCustomerAsync(MySqlConnection cn,MySqlTransaction tx,CustomerDto x,CancellationToken ct)
    {
        var placeholder=new PasswordHasher<object>().HashPassword(new object(),"123456");
        await ExecuteAsync(cn,tx,"INSERT INTO users(id,name,email,password_hash,phone,address,role,active) VALUES(@id,@name,@email,@hash,@phone,@address,'customer',@active) ON DUPLICATE KEY UPDATE name=VALUES(name),phone=VALUES(phone),address=VALUES(address),active=VALUES(active)",ct,("@id",x.Id),("@name",x.Name),("@email",x.Email.ToLowerInvariant()),("@hash",placeholder),("@phone",x.Phone),("@address",x.Address),("@active",x.Active));
    }

    private static async Task<List<ProductDto>> ReadProductsAsync(MySqlConnection cn,CancellationToken ct){var list=new List<ProductDto>();await using var cmd=new MySqlCommand("SELECT * FROM products ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Name=r.GetString("name"),Subtitle=r.GetString("subtitle"),Brand=r.GetString("brand"),Category=r.GetString("category"),Resolution=r.GetString("resolution"),Connection=r.GetString("connection_type"),Price=r.GetDecimal("price"),OldPrice=r.GetDecimal("old_price"),Stock=r.GetInt32("stock"),Image=r.GetString("image"),Tag=r.GetString("tag"),Angle=r.GetString("angle"),Night=r.GetString("night_mode"),Active=r.GetBoolean("active"),Description=r.GetString("description")});return list;}
    private static async Task<List<CategoryDto>> ReadCategoriesAsync(MySqlConnection cn,CancellationToken ct){var list=new List<CategoryDto>();await using var cmd=new MySqlCommand("SELECT * FROM categories ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Name=r.GetString("name"),Description=r.GetString("description"),Active=r.GetBoolean("active")});return list;}
    private static async Task<List<SupplierDto>> ReadSuppliersAsync(MySqlConnection cn,CancellationToken ct){var list=new List<SupplierDto>();await using var cmd=new MySqlCommand("SELECT * FROM suppliers ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Name=r.GetString("name"),Description=r.GetString("description"),Email=r.GetString("email"),Phone=r.GetString("phone"),Active=r.GetBoolean("active")});return list;}
    private static async Task<List<CustomerDto>> ReadCustomersAsync(MySqlConnection cn,CancellationToken ct){var list=new List<CustomerDto>();await using var cmd=new MySqlCommand("SELECT id,name,email,phone,address,role,active FROM users WHERE role='customer' ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(ReadCustomer(r));return list;}
    private static CustomerDto ReadCustomer(MySqlDataReader r)=>new(){Id=r.GetInt64("id"),Name=r.GetString("name"),Email=r.GetString("email"),Phone=r.GetString("phone"),Address=r.GetString("address"),Role=r.GetString("role"),Active=r.GetBoolean("active")};
    private static async Task<CustomerDto?> FindUserDtoAsync(MySqlConnection cn,long id,CancellationToken ct){await using var cmd=new MySqlCommand("SELECT id,name,email,phone,address,role,active FROM users WHERE id=@id",cn);cmd.Parameters.AddWithValue("@id",id);await using var r=await cmd.ExecuteReaderAsync(ct);return await r.ReadAsync(ct)?ReadCustomer(r):null;}
    private static async Task<List<CouponDto>> ReadCouponsAsync(MySqlConnection cn,CancellationToken ct){var list=new List<CouponDto>();await using var cmd=new MySqlCommand("SELECT * FROM coupons ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Code=r.GetString("code"),Type=r.GetString("discount_type"),Value=r.GetDecimal("discount_value"),Min=r.GetDecimal("min_amount"),Max=r.GetDecimal("max_amount"),Active=r.GetBoolean("active")});return list;}
    private static async Task<List<ArticleDto>> ReadArticlesAsync(MySqlConnection cn,CancellationToken ct){var list=new List<ArticleDto>();await using var cmd=new MySqlCommand("SELECT * FROM articles ORDER BY id",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Title=r.GetString("title"),Category=r.GetString("category"),Image=r.GetString("image"),Published=r.GetBoolean("published"),Body=r.GetString("body")});return list;}
    private static async Task<List<ContactDto>> ReadContactsAsync(MySqlConnection cn,CancellationToken ct){var list=new List<ContactDto>();await using var cmd=new MySqlCommand("SELECT * FROM contacts ORDER BY created_at DESC,id DESC",cn);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("id"),Name=r.GetString("name"),Email=r.GetString("email"),Phone=r.GetString("phone"),Subject=r.GetString("subject"),Message=r.GetString("message"),Status=r.GetString("status"),Reply=r.GetString("reply")});return list;}
    private static async Task<List<CartItemDto>> ReadCartAsync(MySqlConnection cn,long userId,CancellationToken ct){var list=new List<CartItemDto>();await using var cmd=new MySqlCommand("SELECT product_id,quantity FROM carts WHERE user_id=@id",cn);cmd.Parameters.AddWithValue("@id",userId);await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetInt64("product_id"),Quantity=r.GetInt32("quantity")});return list;}
    private static async Task<List<OrderDto>> ReadOrdersAsync(MySqlConnection cn,CancellationToken ct)
    {
        var list=new List<OrderDto>();await using(var cmd=new MySqlCommand("SELECT * FROM orders ORDER BY order_date DESC,created_at DESC",cn)){await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))list.Add(new(){Id=r.GetString("id"),Customer=r.GetString("customer"),Email=r.GetString("email"),ShippingEmail=r.GetString("shipping_email"),Phone=r.GetString("phone"),Address=r.GetString("address"),Note=r.GetString("note"),Date=r.GetDateTime("order_date").ToString("yyyy-MM-dd"),Total=r.GetDecimal("total"),Discount=r.GetDecimal("discount"),Status=r.GetString("status"),Payment=r.GetString("payment"),Paid=r.GetBoolean("paid"),Demo=r.GetBoolean("demo")});}
        var map=list.ToDictionary(x=>x.Id);await using(var cmd=new MySqlCommand("SELECT * FROM order_items ORDER BY order_id",cn)){await using var r=await cmd.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct)){var id=r.GetString("order_id");if(map.TryGetValue(id,out var o))o.Items.Add(new(){Id=r.GetInt64("product_id"),Name=r.GetString("product_name"),Quantity=r.GetInt32("quantity"),Price=r.GetDecimal("price"),Image=r.GetString("image")});}}return list;
    }

    private static async Task ExecuteAsync(MySqlConnection cn,MySqlTransaction? tx,string sql,CancellationToken ct,params (string Name,object? Value)[] values){await using var cmd=new MySqlCommand(sql,cn,tx);foreach(var p in values)cmd.Parameters.AddWithValue(p.Name,p.Value??DBNull.Value);await cmd.ExecuteNonQueryAsync(ct);}
    private static async Task DeleteMissingAsync(MySqlConnection cn,MySqlTransaction tx,string table,IEnumerable<long> ids,CancellationToken ct){var values=ids.Distinct().ToArray();if(values.Length==0)return;var names=values.Select((_,i)=>"@p"+i).ToArray();await using var cmd=new MySqlCommand($"DELETE FROM `{table}` WHERE id NOT IN ({string.Join(',',names)})",cn,tx);for(var i=0;i<values.Length;i++)cmd.Parameters.AddWithValue(names[i],values[i]);await cmd.ExecuteNonQueryAsync(ct);}
    private static async Task DeleteMissingStringsAsync(MySqlConnection cn,MySqlTransaction tx,string table,IEnumerable<string> ids,CancellationToken ct){var values=ids.Distinct().ToArray();if(values.Length==0)return;var names=values.Select((_,i)=>"@s"+i).ToArray();await using var cmd=new MySqlCommand($"DELETE FROM `{table}` WHERE id NOT IN ({string.Join(',',names)})",cn,tx);for(var i=0;i<values.Length;i++)cmd.Parameters.AddWithValue(names[i],values[i]);await cmd.ExecuteNonQueryAsync(ct);}
}
