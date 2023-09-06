# Release Notes

## Future Work

- Public test suite
- Better logs with `logging` and `textwrap`

## Pypi Versions

### 0.1.0 (September 2023)

- Package release on Pypi: https://pypi.org/project/vip-client/

## Past Releases

### August 2023

- Improved version of `VipSession.download_outputs()`:
  - Great speed improvement with *parallel downloads*;
  - Initial timeout to avoid casual freeze when updating the workflow inventory;
- Minor bug corrections.

### June 2023

- Class [`VipLauncher`](#viplauncher) is introduced for specific user needs, as a parent of `VipSession` & `VipCI`;
- Session properties (`session_name`, `pipeline_id`, *etc.*) can be safely accessed and modified in all "`Vip*`" classes;
- A list of available pipelines and detailed informations about each pipeline can be displayed through new class method `show_pipeline()`;

### April 2023
- Class [`VipCI`](#vipci) to interacts with Girder datasets (tailored for CI tests in the ReproVIP project).

### March 2023
- Class [`VipSession`](#vipsession): user-friendly interface to run VIP jobs on local datasets.

### Sept. 2018
- Package [`vip.py`](#vippy): generic methods to interact with the VIP REST API.