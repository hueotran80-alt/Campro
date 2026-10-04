namespace CamPro.Web.Models;

public sealed class StoreState
{
    public List<ProductDto> Products { get; init; } = [];
    public List<CategoryDto> Categories { get; init; } = [];
    public List<SupplierDto> Suppliers { get; init; } = [];
    public List<CustomerDto> Customers { get; init; } = [];
    public List<OrderDto> Orders { get; init; } = [];
    public List<CouponDto> Coupons { get; init; } = [];
    public List<ArticleDto> Articles { get; init; } = [];
    public List<ContactDto> Contacts { get; init; } = [];
    public List<CartItemDto> Cart { get; init; } = [];
    public List<long> Compare { get; init; } = [];
    public CustomerDto? Session { get; init; }
}

public sealed class ProductDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public string Subtitle { get; set; } = "";
    public string Brand { get; set; } = "";
    public string Category { get; set; } = "";
    public string Resolution { get; set; } = "";
    public string Connection { get; set; } = "";
    public decimal Price { get; set; }
    public decimal OldPrice { get; set; }
    public int Stock { get; set; }
    public string Image { get; set; } = "";
    public string Tag { get; set; } = "";
    public string Angle { get; set; } = "";
    public string Night { get; set; } = "";
    public bool Active { get; set; }
    public string Description { get; set; } = "";
}

public sealed class CategoryDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public bool Active { get; set; }
}

public sealed class SupplierDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public bool Active { get; set; }
}

public sealed class CustomerDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Address { get; set; } = "";
    public bool Active { get; set; }
    public string Role { get; set; } = "customer";
}

public sealed class OrderDto
{
    public string Id { get; set; } = "";
    public string Customer { get; set; } = "";
    public string Email { get; set; } = "";
    public string ShippingEmail { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Address { get; set; } = "";
    public string Note { get; set; } = "";
    public string Date { get; set; } = "";
    public List<OrderItemDto> Items { get; set; } = [];
    public decimal Total { get; set; }
    public decimal Discount { get; set; }
    public string Status { get; set; } = "Chờ xử lý";
    public string Payment { get; set; } = "COD";
    public bool Paid { get; set; }
    public bool Demo { get; set; }
}

public sealed class OrderItemDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public int Quantity { get; set; }
    public decimal Price { get; set; }
    public string Image { get; set; } = "";
}

public sealed class CouponDto
{
    public long Id { get; set; }
    public string Code { get; set; } = "";
    public string Type { get; set; } = "percent";
    public decimal Value { get; set; }
    public decimal Min { get; set; }
    public decimal Max { get; set; }
    public bool Active { get; set; }
}

public sealed class ArticleDto
{
    public long Id { get; set; }
    public string Title { get; set; } = "";
    public string Category { get; set; } = "";
    public string Image { get; set; } = "";
    public bool Published { get; set; }
    public string Body { get; set; } = "";
}

public sealed class ContactDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Subject { get; set; } = "";
    public string Message { get; set; } = "";
    public string Status { get; set; } = "Chưa xử lý";
    public string Reply { get; set; } = "";
}

public sealed class CartItemDto
{
    public long Id { get; set; }
    public int Quantity { get; set; }
}

public sealed record LoginRequest(string Email, string Password);
public sealed record RegisterRequest(string Name, string Email, string Password);
public sealed record ChangePasswordRequest(string CurrentPassword, string NewPassword);

