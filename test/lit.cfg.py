# -*- Python -*-

import lit.formats
import lit.util

from lit.llvm import llvm_config
from lit.llvm.subst import ToolSubst
from lit.llvm.subst import FindTool

# Configuration file for the 'lit' test runner.

# name: The name of this test suite.
config.name = 'LLVM_SPIRV'

# testFormat: The test format to use to interpret tests.
config.test_format = lit.formats.ShTest(not llvm_config.use_lit_shell)

# suffixes: A list of file extensions to treat as test files.
config.suffixes = ['.cl', '.ll', '.spt', '.spvasm']

# excludes: A list of directories  and fles to exclude from the testsuite.
config.excludes = ['CMakeLists.txt']

if config.libspirv_dis:
    config.available_features.add('libspirv_dis')

if not config.spirv_skip_debug_info_tests:
    # Direct object generation.
    config.available_features.add('object-emission')
    
    # LLVM can be configured with an empty default triple.
    # Some tests are "generic" and require a valid default triple.
    if config.target_triple:
        config.available_features.add('default_triple')
    
    # Ask llvm-config about asserts.
    llvm_config.feature_config([('--assertion-mode', {'ON': 'asserts'})])

# test_source_root: The root path where tests are located.
config.test_source_root = os.path.dirname(__file__)

# test_exec_root: The root path where tests should be run.
config.test_exec_root = os.path.join(config.test_run_dir, 'test_output')

llvm_config.use_default_substitutions()

# Explicitly set `use_installed` to alleviate downstream CI pipelines of
# any additional environment setup for pre-installed Clang usage.
llvm_config.use_clang(use_installed=True)

config.substitutions.append(('%PATH%', config.environment['PATH']))

tool_dirs = [config.llvm_spirv_dir, config.llvm_tools_dir]

tools = ['llvm-as', 'llvm-dis', 'llvm-spirv', 'not']
if not config.spirv_skip_debug_info_tests:
    tools.extend(['llc', 'llvm-dwarfdump', 'llvm-objdump', 'llvm-readelf', 'llvm-readobj'])

llvm_config.add_tool_substitutions(tools, tool_dirs)

using_spirv_tools = False

if config.spirv_tools_have_spirv_as:
    llvm_config.add_tool_substitutions(['spirv-as'], [config.spirv_tools_bin_dir])
    config.available_features.add('spirv-as')
    using_spirv_tools = True

if config.spirv_tools_have_spirv_dis:
    llvm_config.add_tool_substitutions(['spirv-dis'], [config.spirv_tools_bin_dir])
    config.available_features.add('spirv-dis')
    using_spirv_tools = True

if config.spirv_tools_have_spirv_link:
    llvm_config.add_tool_substitutions(['spirv-link'], [config.spirv_tools_bin_dir])
    config.available_features.add('spirv-link')
    using_spirv_tools = True

# Unlike spirv-{as,dis,link} above, running spirv-val is optional: if spirv-val is
# not available, the test must still run and just skip any spirv-val commands.
if config.spirv_tools_have_spirv_val:
    llvm_config.add_tool_substitutions(['spirv-val'], [config.spirv_tools_bin_dir])
    using_spirv_tools = True
else:
    config.substitutions.append(('spirv-val', ':'))

if not config.llvm_spirv_build_external and config.llvm_build_shared_libs:
    config.available_features.add('pass-plugin')
    config.substitutions.append(
        (
            "%load_spirv_lib",
            "-load-pass-plugin={}/libLLVMSPIRVLib{}".format(
                config.llvm_shlib_dir, config.llvm_plugin_ext
            ),
        )
    )

llvm_config.with_system_environment('LD_LIBRARY_PATH')
if using_spirv_tools:
    llvm_config.with_environment('LD_LIBRARY_PATH', config.spirv_tools_lib_dir, append_path=True)
llvm_config.with_environment('LD_LIBRARY_PATH', config.llvm_spirv_lib_dir, append_path=True)
