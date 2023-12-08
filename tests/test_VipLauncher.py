import unittest
from pathlib import *

try: # Use through unittest
    from vip_client.classes import VipLauncher
except ModuleNotFoundError: # Use as a script
    import sys
    SOURCE_ROOT = str(Path(__file__).parents[1] / "src") # <=> /src/
    sys.path.append(SOURCE_ROOT)
    from vip_client.classes import VipLauncher

# class SessionInputs():
#     """Class to record parameters for a given Session"""

#     def __init__(self, **kwargs) -> None:
#         """Generic constructor"""
#         for key, value in kwargs.items():
#             setattr(self, key, value)
#     # ------------------------------------------------

#     def to_dict(self, *args) -> dict:
#         """Get several parameters at once as a dictionary"""
#         if not args: return self.__dict__
#         else: return {prop: getattr(self, prop) for prop in args}
#     # ------------------------------------------------
# # ------------------------------------------------------------------

class VipLauncher_(VipLauncher):

    # Data paths
    VIP_INPUT_DIR = PurePosixPath("/vip/Home/test-VipLauncher/INPUTS/lcmodel_sample")
    VIP_OUTPUT_DIR = PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS")

    # Variables to keep track of sessions
    SESSION_NBR = 0
    SESSIONS = []
    
    # Constructor
    def __init__(self, *args, **kwargs) -> None:
        self.SESSION_NBR += 1
        if args or kwargs: # For a regular VipLauncher initialization
            super().__init__(*args, **kwargs)
        else: # Initiate with testing inputs
            inputs = self.testing_inputs(self.SESSION_NBR)
            super().__init__(**inputs)
            self.input_properties = inputs
            self.output_properties = self.get_properties()
        # Append to session register
        self.SESSIONS.append(self)
    # ------------------------------------------

    # Basic inputs for VipLauncher
    def testing_inputs(self, session_number) -> dict:
        session_name = "Test_VipLauncher_" + str(session_number)
        return {
            'session_name': session_name,
            'output_dir' : self.VIP_OUTPUT_DIR / session_name,
            'pipeline_id' : "LCModel/0.1",
            'input_settings': {
                # Regular path
                "zipped_folder": self.VIP_INPUT_DIR / "basis.zip", 
                # String path
                "basis_file": str(self.VIP_INPUT_DIR / "Basis_117T.basis"), 
                # List of paths
                "signal_file": [ (self.VIP_INPUT_DIR / s) for s in (
                    "signals/Rec001.RAW",  
                    "signals/Rec002.RAW"
                    ) 
                ],
                # List of a single string
                "control_file": [str(self.VIP_INPUT_DIR / "parameters/fit_117T_A.control")]
            }
        }
    # ------------------------------------------

    # Oracle for properties values
    def get_properties(self) -> dict:
        """
        Get session properties as they should be returned by the getter functions
        """
        # Function to parse a single element
        def get_element(element):
            if isinstance(element, dict):
                return {key: get_element(value) for key, value in element.items()}
            elif isinstance(element, list):
                return [get_element(value) for value in element]
            elif element is None:
                return None
            else:
                return str(element)
        # Return
        return {prop: get_element(value) for prop, value in self.input_properties.items()}
    # ------------------------------------------

    # Destructor
# ------------------------------------------------------------------


class Test_VipLauncher(unittest.TestCase):

    __name__ = "Test_VipLauncher"

    @classmethod
    def setUpClass(cls) -> None:
        # Handshake with VIP
        VipLauncher.init(api_key="VIP_API_KEY")

    @classmethod
    def tearDownClass(cls) -> None:
        for session in VipLauncher_.SESSIONS:
            # Clean temporary data on VIP
            session.finish()
    # ------------------------------------------------

    # Function Testing

    def test_run_and_finish(self):
        # Launch a Full Session Run
        s = VipLauncher_().run_session()
        # Check the Results
        self.assertFullRun(s)
        # Finish the Session
        s.finish(timeout=50)
        # Check Deletion
        self.assertFinish(s)
    # ------------------------------------------------
        
    def test_backup(self):
        # Return if backup is disabled
        if VipLauncher_._BACKUP_LOCATION is None:
            return
        # Create session
        s1 = VipLauncher_()
        # Backup
        s1._save()
        # Load backup
        s2 = VipLauncher_(output_dir=s1.output_dir)
        # Check parameters
        self.checkProperties(s2, s1.output_properties)
    # ------------------------------------------------

    # Public interface for properties

    def test_properties_interface(self):
        """
        Tests tha an attribute can be accessed, set and deleted 
        according to the interface rules set in @property
        """
        # Copy the first session
        s = VipLauncher_()
        # Backup the inputs
        backup = s.input_properties
        # Run a subtest for each property
        for prop in s.input_properties:
            with self.subTest(property=prop):
                setattr(s, prop, None) # Calls deleter
                self.assert_(getattr(s, prop) is None) # Public attribute must be None
                self.failIf(s._is_defined("_" + prop)) # Private attribute must be unset
                setattr(s, prop, backup[prop]) # Reset
        # Test correct reset
        self.assertEqual(s.get_properties(), s.output_properties)
    # ------------------------------------------------

    # Display

    def test_log_wrapper(self):
        """Tests that VipLauncher._printc correctly uses `textwrap.TextWrapper.fill()`"""
        import textwrap
        # Test wrapper & text
        wrapper = textwrap.TextWrapper(
            width = 70,
            initial_indent = '    ',
            subsequent_indent = '',
            max_lines = 5,
            drop_whitespace = False,
            replace_whitespace = False,
            break_on_hyphens = False,
            break_long_words = False
        )
        text = """Parses the input settings, i.e.:
        - Converts all input paths (local or VIP) to PathLib objects 
            and write them relatively to their input directory. For example:
            '/vip/Home/API/INPUTS/my_signals/signal001' becomes: 'my_signals/signal001'
        - Leaves the other parameters untouched.\n"""
        # Setup temporary files
        f1, f2 = Path("tmp/test_1.txt"), Path("tmp/test_2.txt")
        if not f1.parent.is_dir():
            f1.parent.mkdir()
        # Write
        with f1.open("w") as t1, f2.open("w") as t2:
            print(wrapper.fill(text), end="", file=t1) # oracle
            VipLauncher._printc(text, end="", wrapper=wrapper, file=t2) # test 
        # Read 
        with f1.open("r") as t1, f2.open("r") as t2:   
            self.assertEqual(t1.read(), t2.read())
        # End : Delete temporary files
        f1.unlink()
        f2.unlink()
        try: f1.parent.rmdir()
        except: pass
    # ------------------------------------------------

    # Robustness testing

    # Conflicts
    def test_backup_with_conflicts(self):
        # Return if backup is disabled
        if VipLauncher_._BACKUP_LOCATION is None:
            return
        # Create session
        s1 = VipLauncher_()
        # Backup
        s1._save()
        # Load backup with conflicting session name
        s2 = VipLauncher_(output_dir=s1.output_dir, session_name="other-name")
        # Check parameters
        self.checkProperties(s2, s1.output_properties)
    # ------------------------------------------------

    # Public interface for properties
    def test_properties_interface_with_conflicts(self):
        return # TODO
        s = VipLauncher_.SESSIONS[0]
        # Backup the inputs
        backup = s.input_properties
        # Run a subtest for each property
        for prop in s.input_properties:
            with self.subTest(property=prop):
                setattr(s, prop, None) # Calls deleter
                self.assert_(getattr(s, prop) is None) # Public attribute must be None
                self.failIf(s._is_defined("_" + prop)) # Private attribute must be unset
                setattr(s, prop, backup[prop]) # Reset
        # Test correct reset
        self.assertEqual(s.get_properties(), s.output_properties)
    # ------------------------------------------------

    # UTILS

    # Function to assert if a file exists
    def assertExists(self, path, location):
        return self.assert_(VipLauncher._exists(path, location))
    # ------------------------------------------------
    
    # Function to assert if a file does not exists
    def assertNotExists(self, path, location):
        return self.failIf(VipLauncher._exists(path, location))
    # ------------------------------------------------

    # Function to assert full run success
    def assertFullRun(self, s: VipLauncher):
        """
        Asserts that a full run worked by checking output files
        """
        # Output directory & Metadata
        self.assertExists(s._vip_output_dir, "vip")
        if s._BACKUP_LOCATION is not None:
            self.assertExists(s._vip_output_dir / s._SAVE_FILE, s._BACKUP_LOCATION)
        # Browse output files
        self.assert_(s.workflows)
        for wid in s.workflows:
            # Workflow finished
            self.assertEqual(s.workflows[wid]["status"], "Finished")
            # Output exists
            self.assert_(s.workflows[wid]["outputs"])
            for output in s.workflows[wid]["outputs"]:
                # File exists
                self.assertExists(PurePosixPath(output["path"]), "vip")
    # ------------------------------------------------

    def checkProperties(self, session: VipLauncher_, properties: dict):
        """Assert that all parameters match"""
        p = properties
        s = session._get(*(p.keys()))
        return self.assertDictEqual(s, p)
    # ------------------------------------------------

    # Function to assert full run success
    def assertFinish(self, s: VipLauncher):
        """
        Asserts that a full run worked by checking output files
        """
        # Local output directory does not exist
        self.assertNotExists(s.vip_output_dir, "vip")
        # Browse output files
        self.assert_(s.workflows)
        for wid in s.workflows:
            # Workflow removed
            self.assert_(s.workflows[wid]["status"] == "Removed")
            # Output exists
            self.assert_(s.workflows[wid]["outputs"])
            for output in s.workflows[wid]["outputs"]:
                # File exists
                self.assertNotExists(PurePosixPath(output["path"]), "vip")
    # ------------------------------------------------
    

if __name__=="__main__":
    unittest.main()

   
