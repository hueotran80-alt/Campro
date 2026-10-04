namespace CamPro.Web.Options;

public sealed class DatabaseOptions
{
    public const string SectionName = "Database";
    public string Server { get; init; } = "127.0.0.1";
    public uint Port { get; init; } = 3306;
    public string Database { get; init; } = "campro_csharp";
    public string User { get; init; } = "root";
    public string Password { get; init; } = "";
}
