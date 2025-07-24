import itertools

import attr
import yaml

from arena_simulation_setup.shared import DynamicObstacle, Obstacle, Pose

from arena_simulation_setup import ProviderBase


@attr.define
class RobotGoal:
    start: Pose
    goal: Pose

    @classmethod
    def parse(cls, obj: dict) -> "RobotGoal":
        return cls(
            start=Pose.parse(obj.get("start", [])),
            goal=Pose.parse(obj.get("goal", [])),
        )


@attr.define
class Scenario:
    static: list[Obstacle]
    dynamic: list[DynamicObstacle]
    robots: list[RobotGoal]


class ScenarioProvider(ProviderBase):
    def load(self) -> "Scenario":
        with open(self.path, 'r') as f:
            scenario = yaml.safe_load(f)

        return Scenario(
            static=[
                Obstacle.parse(
                    obs,
                )
                for obs
                in itertools.chain(
                    scenario.get("obstacles", {}).get("static", []),
                    scenario.get("obstacles", {}).get("interactive", [])
                )
            ],
            dynamic=[
                DynamicObstacle.parse(obs)
                for obs
                in scenario.get("obstacles", {}).get("dynamic", [])
            ],
            robots=[
                RobotGoal.parse(robot)
                for robot
                in scenario.get("robots", [])
            ]
        )
