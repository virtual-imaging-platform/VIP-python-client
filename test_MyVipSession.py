import unittest
import os
import sys
from pathlib import *
sys.path.append(str(Path(".").resolve().absolute()))
from VipSession import VipSession


class TestSessionUnits(unittest.TestCase):

    def test_vip_basename(self):
        for ex in ["", "/", "/a", "/a/", "/a/b", "/a/b/", "a", "a/", "a/b", "a/b/"]:
            self.assertEqual(os.path.basename(ex), VipSession._vip_basename(ex),
            f"'{ex}' -> '{os.path.basename(ex)}' | '{VipSession._vip_basename(ex)}'")

    def test_vip_dirname(self):
        for ex in ["", "/", "/a", "/a/", "/a/b", "/a/b/", "a", "a/", "a/b", "a/b/"]:
            self.assertEqual(os.path.dirname(ex), VipSession._vip_dirname(ex),
            f"'{ex}' -> '{os.path.dirname(ex)}' | '{VipSession._vip_dirname(ex)}'")

    def test_vip_path_join(self):
        """
        The output of Session_vip_path_join perfectly mimics the output of os.path.join,
        except when multiple slashes ("///") are given as arguments.
        """
        for ex in [
            # Regular cases
            ("a",), ("a", "b",), ("a/b","c","d"), ("a/a", "b/b"), ("a", "b", "c/d"),
            # Empty strings
            ("",), ("", ""), ("", "a"), ("a", ""), ("a", "", "b"), ("a", "", "b", ""), ("", "a", "", "b", ""), 
            # Slashes
            ("/",), ("/", "a"), ("a", "/"), ("/", "/"), ("a/", ""), ("", "a/", ""), ("", "a/", "", "b/"), ("a/", "b/", "c/"), ("/a/", "/b/", "/c/"),
            # Absolute paths
            ("/a", "b", "c"), ("a", "/b/c", "d"), ("/a", "b/c", "/d"), ("/a", "/b", "c/d"),
            ]:
            self.assertEqual(os.path.join(*ex), VipSession._vip_path_join(*ex),
            f"'{ex}' -> '{os.path.join(*ex)}' | '{VipSession._vip_path_join(*ex)}'")


if __name__=="__main__":
    # unittest.main()
    # LCModel
    my_input_dir = Path("tests/data/lcmodel_sample")
    my_settings = {
        "zipped_folder" : "tests/data/lcmodel_sample/basis.zip",
        "basis_file" : my_input_dir / "Basis_117T.basis",
        "signal_file" : list((my_input_dir / "signals").iterdir()),
        "control_file" : PurePath("parameters/fit_117T_A.control"),
    }
    VipSession.init("VIP_API_KEY")
    sess = VipSession(
        session_name="tests-VipSession",
        pipeline_id="LCModel/0.1"
    )

    sess.upload_inputs(input_dir=my_input_dir,)
    sess.launch_pipeline(input_settings=my_settings)
    sess.download_outputs(get_status=["Finished", "Running"])
    VipSession("test-VipSession").display()
    VipSession("test-VipSession").monitor_workflows(refresh_time=2)
    sess.download_outputs()

    VipSession(
        session_name="test-VipSession-2", 
        pipeline_id="LCModel/0.1", 
        input_settings=my_settings
    ).get_inputs(sess).display().run_session(update_files=False).finish()

    sess.finish()

    # sess = (
    #     # 1. Create a session
    #     VipSession(session_name="test-lcmodel-2")
    #     # 2. Upload your data on VIP servers
    #     .upload_inputs(input_dir="examples/data/lcmodel_sample")
    #     # 3. Launch a pipeline on VIP
    #     .launch_pipeline(pipeline_id="LCModel/0.1", input_settings=my_settings)
    #     # 4. Monitor its progress on VIP until all executions are over 
    #     .monitor_workflows(refresh_time=2)
    #     # 5. Download the outputs from VIP servers when all executions are over
    #     .download_outputs()
    # )
    # sess.display_properties().finish(timeout=200)

   
