"""Quick test to verify server responds to initialize."""
import subprocess, sys, json, os, threading

proc = subprocess.Popen(
    [sys.executable, 'bundled/tool/lsp_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=os.getcwd()
)

init_request = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'initialize',
    'params': {
        'processId': os.getpid(),
        'rootUri': 'file:///tmp',
        'capabilities': {},
        'initializationOptions': {
            'settings': [],
            'globalSettings': {}
        }
    }
}

body = json.dumps(init_request)
header = "Content-Length: %d\r\n\r\n" % len(body)
msg = (header + body).encode('utf-8')
proc.stdin.write(msg)
proc.stdin.flush()

def read_messages():
    data = b''
    msgs = []
    while len(msgs) < 20:
        chunk = proc.stdout.read(1)
        if not chunk:
            break
        data += chunk
        while b'\r\n\r\n' in data:
            header_part, rest = data.split(b'\r\n\r\n', 1)
            length = None
            for line in header_part.split(b'\r\n'):
                if line.lower().startswith(b'content-length:'):
                    length = int(line.split(b':')[1].strip())
            if length is None:
                break
            if len(rest) < length:
                need = length - len(rest)
                more = proc.stdout.read(need)
                rest += more
            body_bytes = rest[:length]
            data = rest[length:]
            parsed = json.loads(body_bytes)
            msgs.append(parsed)
            method = parsed.get('method', 'RESPONSE')
            msg_id = parsed.get('id', 'N/A')
            print("MSG %d: method=%s id=%s" % (len(msgs), method, msg_id))
            if 'result' in parsed and parsed.get('id') == 1:
                print('Got initialize response!')
                print('Capabilities keys:', list(parsed['result'].get('capabilities', {}).keys()))
                return msgs
            if 'error' in parsed and parsed.get('id') == 1:
                print('Got ERROR response:', parsed['error'])
                return msgs
    return msgs

t = threading.Thread(target=read_messages)
t.start()
t.join(timeout=15)

if t.is_alive():
    print('TIMEOUT - server hung!')
    stderr = proc.stderr.read(4096) if proc.stderr else b''
    print('Stderr:', stderr.decode('utf-8', errors='replace')[:1000])

proc.kill()
