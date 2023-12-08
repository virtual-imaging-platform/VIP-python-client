from test_VipLauncher import Test_VipLauncher, VipLauncher_

class Test_VipSession(Test_VipLauncher):
    # Test upload / download
    # Test portability between sessions

    pass
    
    # @classmethod
    # def tearDownClass(cls) -> None:
    #     for session in VipLauncher_.SESSIONS:
    #         # Clean temporary data on VIP
    #         session.finish()
    #         # Clean local data
    #         session._output_dir.unlink()