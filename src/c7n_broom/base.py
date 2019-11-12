"""
Base module
"""

import logging

import c7n_broom.util


_LOGGER = logging.getLogger(__name__)
REGION_MAP = c7n_broom.util.get_region_names()

# @dataclasses.dataclass(eq=False)
# class Settings:
#     """ c7n Broom Settings"""

#     config: C7nConfig

#     session: boto3.Session = dataclasses.field(init=False)

#     def __post_init__(self):

#         self.session = boto3.Session(
#             region_name=self.config.region, profile_name=self.config.profile
#         )

#         if bool(not self.config.regions):
#             self.config.regions = util.regions_accessible(session=self.session)
