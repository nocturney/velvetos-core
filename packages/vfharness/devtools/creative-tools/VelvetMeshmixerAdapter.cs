using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

class VelvetMeshmixerAdapter
{
    const int RequestPort = 0xAFCF;
    const int ResponsePort = 0xAFDF;
    const string VelvetRoot = @"D:\Velvet";
    const string AcceptanceGate = @"D:\Velvet\State\CreativeTools\Meshmixer\acceptance.enabled";

    sealed class Client : IDisposable
    {
        readonly UdpClient send;
        readonly UdpClient recv;
        readonly IPEndPoint remote;

        public Client()
        {
            remote = new IPEndPoint(IPAddress.Loopback, RequestPort);
            send = new UdpClient(new IPEndPoint(IPAddress.Any, 0));
            recv = new UdpClient();
            recv.ExclusiveAddressUse = true;
            recv.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, false);
            recv.Client.Bind(new IPEndPoint(IPAddress.Loopback, ResponsePort));
            recv.Client.ReceiveTimeout = 3000;
        }

        public int Execute(StoredCommands cmd)
        {
            var serializer = new BinarySerializer();
            cmd.Store(serializer);
            byte[] payload = serializer.buffer().ToArray<byte>();
            send.Send(payload, payload.Length, remote);

            IPEndPoint from = new IPEndPoint(IPAddress.Any, 0);
            byte[] response = recv.Receive(ref from);
            var resultBuf = new vectorub(response);
            serializer.setBuffer(resultBuf);
            cmd.Restore_Results(serializer);
            return response.Length;
        }

        public void Dispose()
        {
            recv.Close();
            send.Close();
        }
    }

    static string JsonEscape(string s)
    {
        if (s == null) return "null";
        return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n") + "\"";
    }

    static void Print(string json) { Console.WriteLine(json); }

    static string SafePath(string path, string[] extensions, bool mustExist)
    {
        string full = Path.GetFullPath(path);
        string root = Path.GetFullPath(VelvetRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!full.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Path must stay under D:\\Velvet");
        if (extensions != null && extensions.Length > 0 &&
            !extensions.Contains(Path.GetExtension(full), StringComparer.OrdinalIgnoreCase))
            throw new InvalidOperationException("Unsupported file extension");
        if (mustExist && !File.Exists(full))
            throw new FileNotFoundException("Input file not found", full);
        return full;
    }

    static int Probe(Client c)
    {
        var cmd = new StoredCommands();
        uint key = cmd.AppendQueryCommand_ConvertScalarToWorld(1.0f);
        int bytes = c.Execute(cmd);
        var result = new floatArray(1);
        bool ok = cmd.GetQueryResult_ConvertScalarToWorld(key, result.cast());
        float value = result.getitem(0);
        Print("{\"status\":\"" + (ok ? "PASS" : "FAIL") + "\",\"ok\":" + (ok ? "true" : "false") + ",\"operation\":\"probe\",\"query\":\"ConvertScalarToWorld\",\"value\":" + value.ToString(CultureInfo.InvariantCulture) + ",\"response_bytes\":" + bytes + "}");
        return ok ? 0 : 4;
    }

    static List<int> ListObjectsInternal(Client c, out bool parsed, out int bytes)
    {
        var cmd = new StoredCommands();
        uint key = cmd.AppendSceneCommand_ListObjects();
        bytes = c.Execute(cmd);
        var v = new vectori();
        parsed = cmd.GetSceneCommandResult_ListObjects(key, v);
        return v.ToList();
    }

    static int ListObjects(Client c)
    {
        bool parsed; int bytes;
        var ids = ListObjectsInternal(c, out parsed, out bytes);
        string arr = "[" + String.Join(",", ids) + "]";
        Print("{\"ok\":true,\"operation\":\"list\",\"parsed\":" + (parsed ? "true" : "false") + ",\"object_ids\":" + arr + ",\"count\":" + ids.Count + ",\"response_bytes\":" + bytes + "}");
        return 0;
    }

    static string GetObjectName(Client c, int id)
    {
        var cmd = new StoredCommands();
        uint key = cmd.AppendSceneCommand_GetObjectName(id);
        c.Execute(cmd);
        var name = new vectorub();
        bool ok = cmd.GetSceneCommandResult_GetObjectName(key, name);
        if (!ok) return null;
        byte[] b = name.ToArray();
        if (b.Length > 0 && b[b.Length - 1] == 0) Array.Resize(ref b, b.Length - 1);
        return Encoding.UTF8.GetString(b);
    }

    static int GetCount(Client c, int id, bool vertices)
    {
        var cmd = new StoredCommands();
        uint key = vertices ? cmd.AppendSceneCommand_GetVertexCount(id) : cmd.AppendSceneCommand_GetTriangleCount(id);
        c.Execute(cmd);
        var r = new any_result();
        bool ok = vertices ? cmd.GetSceneCommandResult_GetVertexCount(key, r) : cmd.GetSceneCommandResult_GetTriangleCount(key, r);
        return ok ? r.i : -1;
    }

    static int Info(Client c, int id)
    {
        string name = GetObjectName(c, id);
        int vertices = GetCount(c, id, true);
        int triangles = GetCount(c, id, false);
        bool ok = name != null && vertices >= 0 && triangles >= 0;
        Print("{\"ok\":" + (ok ? "true" : "false") + ",\"operation\":\"info\",\"id\":" + id + ",\"name\":" + JsonEscape(name) + ",\"vertices\":" + vertices + ",\"triangles\":" + triangles + "}");
        return ok ? 0 : 4;
    }

    static int Import(Client c, string path)
    {
        string input = SafePath(path, new[] { ".obj", ".stl", ".ply" }, true);
        var cmd = new StoredCommands();
        uint key = cmd.AppendSceneCommand_AppendMeshFile(input);
        int bytes = c.Execute(cmd);
        var ids = new vectori();
        bool ok = cmd.GetSceneCommandResult_AppendMeshFile(key, ids);
        var list = ids.ToList();
        Print("{\"ok\":" + (ok ? "true" : "false") + ",\"operation\":\"import\",\"path\":" + JsonEscape(input) + ",\"object_ids\":[" + String.Join(",", list) + "],\"count\":" + list.Count + ",\"response_bytes\":" + bytes + "}");
        return ok && list.Count > 0 ? 0 : 4;
    }

    static int Screenshot(Client c, string path)
    {
        string output = SafePath(path, new[] { ".png" }, false);
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        if (File.Exists(output)) File.Delete(output);
        var cmd = new StoredCommands();
        cmd.AppendSceneCommand_SaveScreenShot(output);
        int bytes = c.Execute(cmd);
        for (int i = 0; i < 30 && !File.Exists(output); i++) Thread.Sleep(100);
        long size = File.Exists(output) ? new FileInfo(output).Length : 0;
        bool ok = size > 0;
        Print("{\"ok\":" + (ok ? "true" : "false") + ",\"operation\":\"screenshot\",\"path\":" + JsonEscape(output) + ",\"bytes\":" + size + ",\"response_bytes\":" + bytes + "}");
        return ok ? 0 : 4;
    }

    static int AcceptanceClear(Client c)
    {
        if (!File.Exists(AcceptanceGate))
            throw new InvalidOperationException("Acceptance gate is not enabled");
        var cmd = new StoredCommands();
        cmd.AppendSceneCommand_Clear();
        int bytes = c.Execute(cmd);
        bool parsed; int listBytes;
        var after = ListObjectsInternal(c, out parsed, out listBytes);
        bool ok = after.Count == 0;
        Print("{\"ok\":" + (ok ? "true" : "false") + ",\"operation\":\"acceptance-clear\",\"remaining\":" + after.Count + ",\"response_bytes\":" + bytes + "}");
        return ok ? 0 : 4;
    }

    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("Usage: VelvetMeshmixerAdapter.exe probe|list|info <id>|import <path>|screenshot <path>|acceptance-clear");
            return 64;
        }

        bool created;
        using (var mutex = new Mutex(true, @"Global\VelvetMeshmixer45023", out created))
        {
            bool ownsMutex = created;
            if (!created)
            {
                ownsMutex = mutex.WaitOne(5000);
                if (!ownsMutex)
                {
                    Console.Error.WriteLine("Meshmixer adapter is busy");
                    return 75;
                }
            }
            try
            {
                using (var client = new Client())
                {
                    string op = args[0].ToLowerInvariant();
                    if (op == "probe") return Probe(client);
                    if (op == "list") return ListObjects(client);
                    if (op == "info" && args.Length == 2) return Info(client, Int32.Parse(args[1], CultureInfo.InvariantCulture));
                    if (op == "import" && args.Length == 2) return Import(client, args[1]);
                    if (op == "screenshot" && args.Length == 2) return Screenshot(client, args[1]);
                    if (op == "acceptance-clear" && args.Length == 1) return AcceptanceClear(client);
                    throw new InvalidOperationException("Unsupported operation or arguments");
                }
            }
            catch (SocketException ex)
            {
                Console.Error.WriteLine("SOCKET_ERROR " + ex.SocketErrorCode + " " + ex.Message);
                return 2;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("ERROR " + ex.GetType().Name + " " + ex.Message);
                return 3;
            }
            finally
            {
                if (ownsMutex) mutex.ReleaseMutex();
            }
        }
    }
}
