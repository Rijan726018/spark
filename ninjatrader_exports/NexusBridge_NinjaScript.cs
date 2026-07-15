// ============================================================================
// NexusBridge — NinjaTrader 8 Indicator
// Drop this file into:
//   Documents\NinjaTrader 8\bin\Custom\Indicators\
// Then compile (Tools > Edit NinjaScript > Indicators) and add to any chart.
//
// Streams BAR + EXEC data to Nexus Algo Terminal (port 9090 by default).
// Compatible with the same TCP protocol used by the NT Data Feeder 8 bridge.
// ============================================================================

#region Using declarations
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using NinjaTrader.Cbi;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
    public class NexusBridge : Indicator
    {
        private TcpClient       _client;
        private NetworkStream   _stream;
        private Thread          _connectThread;
        private bool            _running;

        // ── Parameters (set in NT indicator properties) ─────────────────────
        [NinjaScriptProperty]
        [Display(Name="Host", GroupName="Nexus Bridge", Order=0)]
        public string Host { get; set; } = "127.0.0.1";

        [NinjaScriptProperty]
        [Display(Name="Port", GroupName="Nexus Bridge", Order=1)]
        public int Port { get; set; } = 9090;

        [NinjaScriptProperty]
        [Display(Name="AlgoId", GroupName="Nexus Bridge", Order=2)]
        public string AlgoId { get; set; } = "001";

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Nexus Algo Terminal data bridge — streams bars and executions.";
                Name        = "NexusBridge";
                Calculate   = Calculate.OnBarClose;
                IsOverlay   = true;
            }
            else if (State == State.DataLoaded)
            {
                _running = true;
                _connectThread = new Thread(ConnectLoop) { IsBackground = true };
                _connectThread.Start();
            }
            else if (State == State.Terminated)
            {
                _running = false;
                try { _stream?.Close(); _client?.Close(); } catch { }
            }
        }

        private void ConnectLoop()
        {
            while (_running)
            {
                try
                {
                    _client = new TcpClient();
                    _client.Connect(Host, Port);
                    _stream = _client.GetStream();
                    // Stay connected until disconnected
                    while (_running && _client.Connected)
                        Thread.Sleep(500);
                }
                catch
                {
                    // Retry every 3 s
                    Thread.Sleep(3000);
                }
            }
        }

        private void Send(string line)
        {
            try
            {
                if (_stream == null || !_client.Connected) return;
                byte[] data = Encoding.UTF8.GetBytes(line + "\n");
                _stream.Write(data, 0, data.Length);
            }
            catch { /* will reconnect */ }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < 1 || State != State.Realtime) return;

            long ts = (long)(Time[0].ToUniversalTime()
                        .Subtract(new DateTime(1970,1,1,0,0,0,DateTimeKind.Utc))
                        .TotalSeconds);

            // Send completed bar
            Send($"BAR|{Instrument.FullName}|{Open[0]:F2}|{High[0]:F2}|{Low[0]:F2}|{Close[0]:F2}|{Volume[0]:F0}|{ts}");
        }

        /// <summary>
        /// Call this from an automated strategy to report a trade execution.
        /// e.g.: (Indicators["NexusBridge"] as NexusBridge)?.ReportExecution("BUY", 21505.0, 1);
        /// </summary>
        public void ReportExecution(string side, double price, int qty)
        {
            long ts = (long)(DateTime.UtcNow
                        .Subtract(new DateTime(1970,1,1,0,0,0,DateTimeKind.Utc))
                        .TotalSeconds);
            Send($"EXEC|{AlgoId}|{Instrument.FullName}|{side.ToUpper()}|{price:F2}|{qty}|{ts}");
        }
    }
}
