import nose
import angr
import time

import logging
l = logging.getLogger("angr_tests")

import os
test_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../binaries/tests'))

vfg_0_addresses = {
    'x86_64': 0x40055c
}

def run_vfg_0(arch):
    proj = angr.Project(os.path.join(os.path.join(test_location, arch), "basic_buffer_overflows"),
                 use_sim_procedures=True,
                 default_analysis_mode='symbolic')

    # import ana
    # import pickle

    # # setup datalayer so that we can pickle CFG
    # ana.set_dl(pickle_dir="/tmp")
    # cfg_dump_filename = "/tmp/test_vfg_0_%s.cfg_dump" % arch

    # cfg_loaded = False
    # while not cfg_loaded:
    #     if os.path.isfile(cfg_dump_filename):
    #         try:
    #             cfg = pickle.load(open(cfg_dump_filename, "rb"))
    #             cfg_loaded = True

    #         except Exception:
    #             os.remove(cfg_dump_filename)

    #     else:
    #         cfg = proj.analyses.CFG(context_sensitivity_level=1)
    #         pickle.dump(cfg, open(cfg_dump_filename, "wb"))

    #         cfg_loaded = True

    cfg = proj.analyses.CFG(context_sensitivity_level=1)

    start = time.time()
    function_start = vfg_0_addresses[arch]
    vfg = proj.analyses.VFG(cfg, function_start=function_start, context_sensitivity_level=2, interfunction_level=4)
    end = time.time()
    duration = end - start

    l.info("VFG generation done in %f seconds.", duration)

    # TODO: These are very weak conditions. Make them stronger!
    nose.tools.assert_greater(len(vfg.result['final_states']), 0)
    states = vfg.result['final_states']
    nose.tools.assert_equal(len(states), 2)
    stack_check_fail = proj._extern_obj.get_pseudo_addr('simuvex.procedures.libc___so___6.__stack_chk_fail.__stack_chk_fail')
    nose.tools.assert_equal(set([ s.se.exactly_int(s.ip) for s in states ]),
                            {
                                stack_check_fail,
                                0x4005b4
                            })

    state = [ s for s in states if s.se.exactly_int(s.ip) == 0x4005b4 ][0]
    nose.tools.assert_true(state.se.is_true(state.stack_read(12, 4) >= 0x28))

def test_vfg_0():
    for arch in vfg_0_addresses:
        yield run_vfg_0, arch

if __name__ == "__main__":
    # logging.getLogger("simuvex.plugins.abstract_memory").setLevel(logging.DEBUG)
    # logging.getLogger("simuvex.plugins.symbolic_memory").setLevel(logging.DEBUG)
    logging.getLogger("angr.analyses.cfg").setLevel(logging.DEBUG)
    logging.getLogger("angr.analyses.vfg").setLevel(logging.DEBUG)
    # Temporarily disable the warnings of claripy backend
    logging.getLogger("claripy.backends.backend").setLevel(logging.ERROR)
    logging.getLogger("claripy.claripy").setLevel(logging.ERROR)

    for test_func, arch_name in test_vfg_0():
        test_func(arch_name)
