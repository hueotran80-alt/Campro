using CamPro.Web.Options;
using Microsoft.Extensions.Options;
using MySqlConnector;

namespace CamPro.Web.Data;

public sealed class MySqlConnectionFactory(IOptions<DatabaseOptions> options)
{
    private readonly DatabaseOptions _options = options.Value;

    public string DatabaseName => _options.Database;

    public MySqlConnection Create(bool includeDatabase = true)
    {
        var builder = new MySqlConnectionStringBuilder
        {
            Server = _options.Server,
            Port = _options.Port,
            UserID = _options.User,
            Password = _options.Password,
            Database = includeDatabase ? _options.Database : "",
            CharacterSet = "utf8mb4",
            AllowUserVariables = true,
            ConnectionTimeout = 8,
            DefaultCommandTimeout = 30
        };
        return new MySqlConnection(builder.ConnectionString);
    }
}

