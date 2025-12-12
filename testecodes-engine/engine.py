import subprocess, tempfile, os, resource, pwd, ctypes

RUNNERS = {
    "python": {
        "ext": ".py",
        "compile": None,
        "run": lambda path, dir: ["python3", path]
    },
    "c": {
        "ext": ".c",
        "compile": lambda path, dir: ["gcc", path, "-o", os.path.join(dir, "app")],
        "run": lambda path, dir: [os.path.join(dir, "app")]
    }
}


class Engine:
    def __init__(self, cpu, ram, proc):
        self.cpu = cpu 
        self.ram = ram # byte
        self.proc = proc


    def set_limit(self):
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu, self.cpu))
        resource.setrlimit(resource.RLIMIT_AS, (self.ram, self.ram))
        resource.setrlimit(resource.RLIMIT_NPROC, (self.proc, self.proc))

    def drop_network(self):
        libc = ctypes.CDLL("libc.so.6")
        CLONE_NEWNET = 0x40000000
        libc.unshare(CLONE_NEWNET)

    def drop_privileges(self):
        user = pwd.getpwnam("codeduel")
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)

    def sandbox(self):

        self.drop_network()
        self.drop_privileges()
        self.set_limit()

    def run(self, code, language, time=5):
        cfg = RUNNERS[language]

        with tempfile.TemporaryDirectory() as dir:
            path = os.path.join(dir, "app" + cfg["ext"])

            with open(path, "w") as f:
                f.write(code)

            # compilar se necessário
            if cfg["compile"]:
                subprocess.run(
                    cfg["compile"](path, dir),
                    capture_output=True,
                    text=True,
                    preexec_fn=self.sandbox,
                    timeout=time
                )

            # executar
            res = subprocess.run(
                cfg["run"](path, dir),
                capture_output=True,
                text=True,
                preexec_fn=self.sandbox,
                timeout=time
            )

            return {
                "stdout": res.stdout,
                "stderr": res.stderr
            }



if __name__ == "__main__":

    code = """
print('oi')
    """
    eng = Engine(cpu=2, ram=256*1024*1024, proc=10)
    resposta = eng.run(code=code, language="python")
    print(resposta)