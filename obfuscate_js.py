#!/usr/bin/env python3
"""
JavaScript Obfuscation Tool for ManhwaVerse
===========================================

This script obfuscates JavaScript files to make them harder to read and reverse engineer.
It provides multiple levels of protection while maintaining functionality.

Author: ManhwaVerse Development Team
"""

import os
import re
import base64
import zlib
import random
import string
from pathlib import Path

class JSObfuscator:
    def __init__(self):
        self.string_map = {}
        self.variable_map = {}
        self.function_map = {}
        
    def generate_random_name(self, length=8):
        """Generate a random variable/function name."""
        return ''.join(random.choices(string.ascii_letters + '_', k=length))
    
    def obfuscate_strings(self, content):
        """Obfuscate string literals."""
        def replace_string(match):
            string_content = match.group(1)
            if len(string_content) > 3:  # Only obfuscate longer strings
                if string_content not in self.string_map:
                    # Create a base64 encoded string
                    encoded = base64.b64encode(string_content.encode()).decode()
                    var_name = self.generate_random_name()
                    self.string_map[string_content] = f"atob('{encoded}')"
                return self.string_map[string_content]
            return match.group(0)
        
        # Replace string literals
        content = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', replace_string, content)
        content = re.sub(r"'([^'\\]*(\\.[^'\\]*)*)'", replace_string, content)
        return content
    
    def obfuscate_variables(self, content):
        """Obfuscate variable names (basic level)."""
        # Find common variable patterns
        variables = re.findall(r'\b(let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\b', content)
        
        for var_type, var_name in variables:
            if var_name not in ['window', 'document', 'console', 'localStorage', 'sessionStorage', 'JSON', 'Math', 'Date', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Function', 'Promise', 'fetch', 'XMLHttpRequest', 'Error', 'RegExp', 'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURIComponent', 'decodeURIComponent', 'encodeURI', 'decodeURI', 'escape', 'unescape', 'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval', 'requestAnimationFrame', 'cancelAnimationFrame']:
                if var_name not in self.variable_map:
                    self.variable_map[var_name] = self.generate_random_name()
                content = content.replace(f'{var_type} {var_name}', f'{var_type} {self.variable_map[var_name]}')
        
        return content
    
    def add_dummy_code(self, content):
        """Add dummy code to confuse reverse engineers."""
        dummy_functions = [
            "function _0x{}(a,b){{return a+b;}}".format(self.generate_random_name(4)),
            "var _0x{} = function(){{return Math.random();}}".format(self.generate_random_name(4)),
            "const _0x{} = () => {{console.log('dummy');}}".format(self.generate_random_name(4))
        ]
        
        # Insert dummy code at the beginning
        dummy_code = '\n'.join(dummy_functions) + '\n'
        return dummy_code + content
    
    def add_anti_debug(self, content):
        """Add anti-debugging measures."""
        anti_debug = """
        // Anti-debugging measures
        (function() {
            let devtools = {open: false, orientation: null};
            const threshold = 160;
            setInterval(function() {
                if (window.outerHeight - window.innerHeight > threshold || 
                    window.outerWidth - window.innerWidth > threshold) {
                    if (!devtools.open) {
                        devtools.open = true;
                        console.clear();
                        console.log('%cStop!', 'color: red; font-size: 50px; font-weight: bold;');
                        console.log('%cThis is a browser feature intended for developers.', 'color: red; font-size: 16px;');
                    }
                } else {
                    devtools.open = false;
                }
            }, 500);
        })();
        """
        return anti_debug + content
    
    def minify(self, content):
        """Basic minification."""
        # Remove comments
        content = re.sub(r'//.*?\n', '', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r';\s*}', ';}', content)
        content = re.sub(r'{\s*', '{', content)
        content = re.sub(r'}\s*', '}', content)
        
        return content.strip()
    
    def obfuscate_file(self, input_path, output_path, level='medium'):
        """Obfuscate a JavaScript file."""
        print(f"Obfuscating {input_path}...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply obfuscation based on level
        if level == 'light':
            content = self.minify(content)
        elif level == 'medium':
            content = self.obfuscate_strings(content)
            content = self.minify(content)
        elif level == 'heavy':
            content = self.obfuscate_strings(content)
            content = self.obfuscate_variables(content)
            content = self.add_dummy_code(content)
            content = self.add_anti_debug(content)
            content = self.minify(content)
        
        # Write obfuscated content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Obfuscated file saved to {output_path}")
        print(f"Original size: {len(open(input_path, 'r', encoding='utf-8').read())} bytes")
        print(f"Obfuscated size: {len(content)} bytes")

def main():
    obfuscator = JSObfuscator()
    
    # Create obfuscated directory
    os.makedirs('assets/js/obfuscated', exist_ok=True)
    
    # Obfuscate main JavaScript files
    js_files = [
        'assets/js/main.js',
        'assets/js/components.js'
    ]
    
    for js_file in js_files:
        if os.path.exists(js_file):
            output_file = js_file.replace('assets/js/', 'assets/js/obfuscated/')
            obfuscator.obfuscate_file(js_file, output_file, level='medium')
        else:
            print(f"Warning: {js_file} not found")
    
    print("\nObfuscation complete!")
    print("To use obfuscated files, update your HTML to reference the obfuscated versions.")
    print("Example: <script src='assets/js/obfuscated/main.js'></script>")

if __name__ == "__main__":
    main()
