using Microsoft.AspNetCore.Identity;
using MySqlConnector;

namespace CamPro.Web.Data;

public sealed class DatabaseInitializer(
    MySqlConnectionFactory factory,
    IWebHostEnvironment environment,
    ILogger<DatabaseInitializer> logger)
{
    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        await using (var master = factory.Create(false))
        {
            await master.OpenAsync(cancellationToken);
            var safeName = factory.DatabaseName.Replace("`", "``", StringComparison.Ordinal);
            await using var create = new MySqlCommand(
                $"CREATE DATABASE IF NOT EXISTS `{safeName}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;", master);
            await create.ExecuteNonQueryAsync(cancellationToken);
        }

        await using var connection = factory.Create();
        await connection.OpenAsync(cancellationToken);
        var schemaPath = Path.Combine(environment.ContentRootPath, "Data", "Schema.sql");
        var schema = await File.ReadAllTextAsync(schemaPath, cancellationToken);
        await using (var command = new MySqlCommand(schema, connection))
        {
            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        var hasher = new PasswordHasher<object>();
        await UpsertUserAsync(connection, 1, "Quản trị CAMPRO", "admin@campro.vn", hasher.HashPassword(new object(), "Admin@123"), "0900000000", "CAMPRO", "admin", cancellationToken);
        await UpsertUserAsync(connection, 2, "Nguyễn Minh Anh", "minhanh@example.com", hasher.HashPassword(new object(), "123456"), "0900000001", "24 Nguyễn Văn Cừ, Hà Nội", "customer", cancellationToken);
        await UpsertUserAsync(connection, 3, "Trần Hoàng Nam", "hoangnam@example.com", hasher.HashPassword(new object(), "123456"), "0900000002", "15 Lê Lợi, Đà Nẵng", "customer", cancellationToken);
        await UpsertUserAsync(connection, 4, "Lê Thu Hà", "thuha@example.com", hasher.HashPassword(new object(), "123456"), "0900000003", "80 Nguyễn Trãi, TP. Hồ Chí Minh", "customer", cancellationToken);
        logger.LogInformation("CAMPRO database {Database} is ready.", factory.DatabaseName);
    }

    private static async Task UpsertUserAsync(
        MySqlConnection connection, long id, string name, string email, string passwordHash,
        string phone, string address, string role, CancellationToken cancellationToken)
    {
        const string sql = """
            INSERT INTO users(id,name,email,password_hash,phone,address,role,active)
            VALUES(@id,@name,@email,@password,@phone,@address,@role,1)
            ON DUPLICATE KEY UPDATE name=VALUES(name),phone=VALUES(phone),address=VALUES(address),role=VALUES(role);
            """;
        await using var command = new MySqlCommand(sql, connection);
        command.Parameters.AddWithValue("@id", id);
        command.Parameters.AddWithValue("@name", name);
        command.Parameters.AddWithValue("@email", email);
        command.Parameters.AddWithValue("@password", passwordHash);
        command.Parameters.AddWithValue("@phone", phone);
        command.Parameters.AddWithValue("@address", address);
        command.Parameters.AddWithValue("@role", role);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }
}
