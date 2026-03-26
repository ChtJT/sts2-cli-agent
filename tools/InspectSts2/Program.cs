using System.Reflection;
using System.Runtime.Loader;

var root = args.Length > 0
    ? args[0]
    : Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../"));
var libDir = Path.Combine(root, "lib");
var headlessDir = Path.Combine(root, "Sts2Headless/bin/Debug/net10.0");
var mainAssemblyPath = Path.Combine(libDir, "sts2.dll");
if (!File.Exists(mainAssemblyPath))
{
    Console.Error.WriteLine($"Missing assembly: {mainAssemblyPath}");
    return 1;
}

var loadContext = new InspectLoadContext(libDir, headlessDir);
var assembly = loadContext.LoadFromAssemblyPath(mainAssemblyPath);

var queries = args.Skip(1).ToArray();
if (queries.Length == 0)
{
    queries = new[]
    {
        "AssetCache",
        "PlayerHurtVignetteHelper",
        "NLowHpBorderVfx",
    };
}

foreach (var query in queries)
    DumpSearch(assembly, query);

if (queries.Contains("AssetCache", StringComparer.OrdinalIgnoreCase))
    DumpAssetCacheHolders(assembly);
return 0;

static void DumpSearch(Assembly assembly, string query)
{
    Console.WriteLine($"SEARCH {query}");
    List<Type> matches;
    try
    {
        matches = assembly.GetTypes()
            .Where(t => (t.FullName ?? t.Name).Contains(query, StringComparison.OrdinalIgnoreCase))
            .OrderBy(t => t.FullName)
            .ToList();
    }
    catch (ReflectionTypeLoadException ex)
    {
        matches = ex.Types
            .Where(t => t != null && (t.FullName ?? t.Name).Contains(query, StringComparison.OrdinalIgnoreCase))
            .Cast<Type>()
            .OrderBy(t => t.FullName)
            .ToList();
        foreach (var loaderEx in ex.LoaderExceptions)
            Console.WriteLine($"  LOADER {loaderEx?.GetType().Name}: {loaderEx?.Message}");
    }

    if (matches.Count == 0)
    {
        Console.WriteLine("  <missing>");
        return;
    }

    foreach (var type in matches)
        DumpType(type);
}

static void DumpType(Type type)
{
    Console.WriteLine($"TYPE {type.FullName}");
    Console.WriteLine($"  BaseType: {type.BaseType}");

    foreach (var ctor in type.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
    {
        try { Console.WriteLine($"  CTOR {FormatMethod(ctor)}"); }
        catch (Exception ex) { Console.WriteLine($"  CTOR <error: {ex.GetType().Name}: {ex.Message}>"); }
    }

    foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
    {
        try { Console.WriteLine($"  FIELD {(field.IsStatic ? "static " : "")}{field.FieldType} {field.Name}"); }
        catch (Exception ex) { Console.WriteLine($"  FIELD {field.Name} <error: {ex.GetType().Name}: {ex.Message}>"); }
    }

    foreach (var prop in type.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
    {
        try { Console.WriteLine($"  PROP {(IsStatic(prop) ? "static " : "")}{prop.PropertyType} {prop.Name}"); }
        catch (Exception ex) { Console.WriteLine($"  PROP {prop.Name} <error: {ex.GetType().Name}: {ex.Message}>"); }
    }

    foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
    {
        try { Console.WriteLine($"  METHOD {FormatMethod(method)}"); }
        catch (Exception ex) { Console.WriteLine($"  METHOD {method.Name} <error: {ex.GetType().Name}: {ex.Message}>"); }
    }
}

static string FormatMethod(MethodBase method)
{
    var returnType = method is MethodInfo info ? $"{info.ReturnType} " : string.Empty;
    var staticText = method.IsStatic ? "static " : string.Empty;
    var parameters = string.Join(", ", method.GetParameters().Select(p => $"{p.ParameterType} {p.Name}"));
    return $"{staticText}{returnType}{method.Name}({parameters})";
}

static bool IsStatic(PropertyInfo property)
{
    var accessor = property.GetMethod ?? property.SetMethod;
    return accessor?.IsStatic == true;
}

static void DumpAssetCacheHolders(Assembly assembly)
{
    Console.WriteLine("SEARCH AssetCache holders");
    Type[] types;
    try
    {
        types = assembly.GetTypes();
    }
    catch (ReflectionTypeLoadException ex)
    {
        types = ex.Types.Where(t => t != null).Cast<Type>().ToArray();
    }

    foreach (var type in types.OrderBy(t => t.FullName))
    {
        foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
        {
            if (!field.FieldType.Name.Contains("AssetCache", StringComparison.OrdinalIgnoreCase))
                continue;
            Console.WriteLine($"  FIELD {type.FullName} :: {(field.IsStatic ? "static " : "")}{field.FieldType} {field.Name}");
        }

        foreach (var prop in type.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
        {
            if (!prop.PropertyType.Name.Contains("AssetCache", StringComparison.OrdinalIgnoreCase))
                continue;
            Console.WriteLine($"  PROP {type.FullName} :: {(IsStatic(prop) ? "static " : "")}{prop.PropertyType} {prop.Name}");
        }

        foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
        {
            try
            {
                if (!method.ReturnType.Name.Contains("AssetCache", StringComparison.OrdinalIgnoreCase))
                    continue;
            }
            catch
            {
                continue;
            }

            Console.WriteLine($"  METHOD {type.FullName} :: {FormatMethod(method)}");
        }
    }
}

sealed class InspectLoadContext : AssemblyLoadContext
{
    private readonly string[] _probeDirs;

    public InspectLoadContext(params string[] probeDirs) : base(nameof(InspectLoadContext), isCollectible: true)
    {
        _probeDirs = probeDirs.Where(Directory.Exists).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
    }

    protected override Assembly? Load(AssemblyName assemblyName)
    {
        foreach (var dir in _probeDirs)
        {
            var candidate = Path.Combine(dir, $"{assemblyName.Name}.dll");
            if (File.Exists(candidate))
                return LoadFromAssemblyPath(candidate);
        }
        return null;
    }
}
