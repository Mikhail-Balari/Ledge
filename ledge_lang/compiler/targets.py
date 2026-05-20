"""
Ledge Compilation Targets
==========================
Handles compilation to different deployment targets:
  - Native binary (x86_64, ARM64, ARM32)
  - WebAssembly (WASM)
  - JavaScript (via Emscripten)
  - Serverless (AWS Lambda, Google Cloud Functions)

Each target:
1. Calls compile_to_ir() to get LLVM IR
2. Runs the appropriate toolchain
3. Returns the output artifact path

Prerequisites:
  native:     clang or llc + linker (install: apt install clang)
  wasm:       emcc (install: https://emscripten.org)
  js:         emcc with -s ENVIRONMENT=web
  serverless: clang + zip packaging

When tools are not available, raises TargetNotAvailable with
installation instructions. Never silently fails.
"""

from __future__ import annotations
import os, subprocess, tempfile, shutil
from typing import Optional
from ledge_lang._version import __version__
from .codegen import compile_to_ir


class TargetNotAvailable(Exception):
    """Raised when a compilation target's toolchain is not installed."""
    pass


def _find_tool(*names: str) -> Optional[str]:
    """Find first available tool from the list."""
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def _run_tool(cmd: list, input_data: str = None, cwd: str = None) -> subprocess.CompletedProcess:
    """Run a compilation tool, raising on failure."""
    result = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Tool failed: {' '.join(cmd)}\n"
            f"stderr: {result.stderr}"
        )
    return result


def compile_to_native(source: str, output_path: str = "a.out",
                      target: str = "x86_64", optimize: bool = True) -> str:
    """
    Compile Ledge source to a native binary.
    
    Args:
        source: Ledge source code
        output_path: path for output binary
        target: "x86_64", "arm64", "arm32", "riscv64"
        optimize: enable -O3 optimization
    
    Returns:
        Path to the compiled binary.
    
    Requires:
        clang (recommended) or llc + linker
        Install: sudo apt install clang    (Ubuntu/Debian)
                 brew install llvm         (macOS)
                 choco install llvm        (Windows)
    """
    clang = _find_tool("clang", "clang-15", "clang-14", "clang-16")
    if not clang:
        raise TargetNotAvailable(
            "Native compilation requires clang. Install it:\n"
            "  Ubuntu/Debian: sudo apt install clang\n"
            "  macOS:         brew install llvm\n"
            "  Windows:       choco install llvm\n"
            "  Or use the tree-walker interpreter: ledge run program.ledge"
        )
    
    ir = compile_to_ir(source)
    
    # Target triple mapping
    triple_map = {
        "x86_64":  "x86_64-unknown-linux-gnu",
        "arm64":   "aarch64-unknown-linux-gnu",
        "arm32":   "armv7-unknown-linux-gnueabi",
        "riscv64": "riscv64-unknown-linux-gnu",
        "macos_x86": "x86_64-apple-macosx12.0",
        "macos_arm": "arm64-apple-macosx12.0",
    }
    triple = triple_map.get(target, "x86_64-unknown-linux-gnu")
    
    # Update target triple in IR
    ir = ir.replace(
        'target triple = "x86_64-unknown-linux-gnu"',
        f'target triple = "{triple}"'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ir_path = os.path.join(tmpdir, "program.ll")
        with open(ir_path, 'w') as f:
            f.write(ir)
        
        opt_flag = ["-O3"] if optimize else ["-O0"]
        
        cmd = [clang] + opt_flag + ["-target", triple, ir_path, "-o", output_path,
                "-lm",  # link math library for sqrt, etc.
                "-no-pie"]  # simpler binary format
        
        _run_tool(cmd)
    
    os.chmod(output_path, 0o755)
    return os.path.abspath(output_path)


def compile_to_wasm(source: str, output_path: str = "program.wasm",
                    optimize: bool = True) -> str:
    """
    Compile Ledge source to WebAssembly.
    
    The resulting .wasm file can be:
    - Loaded in a browser with WebAssembly.instantiate()
    - Run with Node.js or Deno
    - Embedded in any WASM runtime (Wasmtime, Wasmer, etc.)
    
    Args:
        source: Ledge source code
        output_path: path for output .wasm file
        optimize: enable optimization
    
    Returns:
        Path to the .wasm file.
    
    Requires:
        emcc (Emscripten)
        Install: https://emscripten.org/docs/getting_started/downloads.html
        Or via emsdk:
          git clone https://github.com/emscripten-core/emsdk.git
          cd emsdk && ./emsdk install latest && ./emsdk activate latest
    """
    emcc = _find_tool("emcc")
    if not emcc:
        # Try wasm32 via clang directly
        clang = _find_tool("clang", "clang-15", "clang-14")
        if clang:
            return _compile_wasm_clang(source, output_path, clang, optimize)
        
        raise TargetNotAvailable(
            "WASM compilation requires Emscripten (emcc). Install it:\n"
            "  git clone https://github.com/emscripten-core/emsdk.git\n"
            "  cd emsdk && ./emsdk install latest && ./emsdk activate latest\n"
            "  source emsdk_env.sh\n"
            "  Then retry: ledge run program.ledge --target wasm"
        )
    
    ir = compile_to_ir(source)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ir_path = os.path.join(tmpdir, "program.ll")
        with open(ir_path, 'w') as f:
            f.write(ir)
        
        opt_flags = ["-O3"] if optimize else ["-O0"]
        
        cmd = [emcc] + opt_flags + [
            ir_path,
            "-o", output_path,
            "-s", "WASM=1",
            "-s", "STANDALONE_WASM=1",
            "-s", "EXPORTED_FUNCTIONS=['_main']",
            "--no-entry",
        ]
        
        _run_tool(cmd)
    
    return os.path.abspath(output_path)


def _compile_wasm_clang(source: str, output_path: str, clang: str, optimize: bool) -> str:
    """Compile to WASM32 via clang's wasm32 target (no emcc needed)."""
    ir = compile_to_ir(source)
    
    # Update for WASM target
    ir = ir.replace(
        'target triple = "x86_64-unknown-linux-gnu"',
        'target triple = "wasm32-unknown-unknown"'
    ).replace(
        'target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"',
        'target datalayout = "e-m:e-p:32:32-i64:64-n32:64-S128"'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ir_path = os.path.join(tmpdir, "program.ll")
        with open(ir_path, 'w') as f:
            f.write(ir)
        
        opt = ["-O3"] if optimize else ["-O0"]
        cmd = [clang] + opt + [
            "--target=wasm32-unknown-unknown",
            "-nostdlib",
            "-Wl,--no-entry",
            "-Wl,--export-all",
            ir_path,
            "-o", output_path,
        ]
        
        _run_tool(cmd)
    
    return os.path.abspath(output_path)


def compile_to_js(source: str, output_path: str = "program.js") -> str:
    """
    Compile Ledge source to JavaScript-compatible WASM bundle.
    
    The output can be loaded directly in a browser or Node.js:
        <script src="program.js"></script>
        // or
        const program = require('./program.js');
    
    Requires: emcc (Emscripten)
    """
    emcc = _find_tool("emcc")
    if not emcc:
        raise TargetNotAvailable(
            "JavaScript/browser compilation requires Emscripten.\n"
            "Install: https://emscripten.org/docs/getting_started/downloads.html"
        )
    
    ir = compile_to_ir(source)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ir_path = os.path.join(tmpdir, "program.ll")
        with open(ir_path, 'w') as f:
            f.write(ir)
        
        cmd = [emcc, "-O3", ir_path, "-o", output_path,
               "-s", "MODULARIZE=1",
               "-s", "EXPORT_NAME=LedgeProgram",
               "-s", "ENVIRONMENT=web,node"]
        
        _run_tool(cmd)
    
    return os.path.abspath(output_path)


def compile_to_serverless(source: str, output_dir: str = "lambda_package",
                          runtime: str = "aws_lambda") -> str:
    """
    Package a Ledge program as a serverless function.
    
    Targets:
        aws_lambda:   AWS Lambda (native binary + bootstrap)
        gcf:          Google Cloud Functions (Node.js WASM wrapper)
        azure:        Azure Functions (Node.js WASM wrapper)
    
    The native binary approach (aws_lambda) is fastest — no interpreter overhead.
    The WASM approach (gcf, azure) is more portable.
    
    Returns:
        Path to the deployment package (.zip)
    
    Requires:
        aws_lambda: clang + zip
        gcf/azure:  emcc + zip
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if runtime == "aws_lambda":
        return _build_lambda_package(source, output_dir)
    elif runtime in ("gcf", "azure"):
        return _build_wasm_serverless(source, output_dir, runtime)
    else:
        raise ValueError(f"Unknown serverless runtime: {runtime}. Use: aws_lambda, gcf, azure")


def _build_lambda_package(source: str, output_dir: str) -> str:
    """Build an AWS Lambda deployment package with native binary."""
    import zipfile
    
    binary_path = os.path.join(output_dir, "bootstrap")
    
    try:
        compile_to_native(source, binary_path, target="x86_64")
    except TargetNotAvailable as e:
        raise TargetNotAvailable(
            f"AWS Lambda packaging failed: {e}\n"
            "For Lambda, you need to compile on Linux or use Docker:\n"
            "  docker run -v $(pwd):/work amazonlinux:2 bash -c \\\n"
            "    'yum install -y clang && ledge run program.ledge --target serverless'"
        )
    
    # Create the Lambda handler bootstrap
    bootstrap_content = f"""#!/bin/sh
# Ledge AWS Lambda bootstrap
# The 'bootstrap' binary IS the program — Lambda custom runtime
exec /var/task/bootstrap "$@"
"""
    
    # Package as zip
    zip_path = os.path.join(output_dir, "ledge_lambda.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(binary_path, "bootstrap")
    
    return zip_path


def _build_wasm_serverless(source: str, output_dir: str, runtime: str) -> str:
    """Build a WASM-based serverless package for GCF/Azure."""
    import zipfile
    import json
    
    wasm_path = os.path.join(output_dir, "program.wasm")
    compile_to_wasm(source, wasm_path)
    
    # Create Node.js wrapper
    handler = """
const fs = require('fs');
const wasmBuffer = fs.readFileSync('./program.wasm');

let instance = null;

async function init() {
    if (!instance) {
        const mod = await WebAssembly.compile(wasmBuffer);
        instance = await WebAssembly.instantiate(mod, {
            env: {
                printf: (fmt, ...args) => {
                    console.log(...args);
                    return 0;
                },
                malloc: (size) => 0,
                free: (ptr) => {},
            }
        });
    }
    return instance;
}

exports.handler = async (event, context) => {
    const inst = await init();
    inst.exports.main();
    return { statusCode: 200, body: 'OK' };
};
"""
    
    handler_path = os.path.join(output_dir, "index.js")
    with open(handler_path, 'w') as f:
        f.write(handler)
    
    pkg_json = {
        "name": "ledge-serverless",
        "version": __version__,
        "main": "index.js",
        "description": "Ledge serverless function"
    }
    with open(os.path.join(output_dir, "package.json"), 'w') as f:
        json.dump(pkg_json, f, indent=2)
    
    # Zip it
    import zipfile
    zip_path = os.path.join(output_dir, f"ledge_{runtime}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in ["program.wasm", "index.js", "package.json"]:
            fpath = os.path.join(output_dir, fname)
            if os.path.exists(fpath):
                zf.write(fpath, fname)
    
    return zip_path


# ── Convenience wrapper ────────────────────────────────────────────────────────

def auto_compile(source: str, output: str, target: str = "native") -> str:
    """
    Compile to the specified target, with helpful error messages.
    
    target options:
        "native"      — native binary for current platform
        "wasm"        — WebAssembly .wasm file  
        "js"          — JavaScript/WASM bundle
        "arm32"       — ARM 32-bit binary
        "arm64"       — ARM 64-bit binary (Apple M1/M2, RPi 4 64-bit)
        "serverless"  — AWS Lambda package
    """
    dispatch = {
        "native":     lambda: compile_to_native(source, output),
        "wasm":       lambda: compile_to_wasm(source, output),
        "js":         lambda: compile_to_js(source, output),
        "arm32":      lambda: compile_to_native(source, output, target="arm32"),
        "arm64":      lambda: compile_to_native(source, output, target="arm64"),
        "serverless": lambda: compile_to_serverless(source, output),
        "lambda":     lambda: compile_to_serverless(source, output, runtime="aws_lambda"),
        "gcf":        lambda: compile_to_serverless(source, output, runtime="gcf"),
    }
    
    fn = dispatch.get(target)
    if not fn:
        available = list(dispatch.keys())
        raise ValueError(f"Unknown target: {target}. Available: {available}")
    
    return fn()
