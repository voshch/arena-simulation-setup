import os
from launch import LaunchDescription
from launch.actions import (GroupAction, IncludeLaunchDescription, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import SetRemap, Node
from launch_ros.substitutions import FindPackageShare

from arena_bringup.substitutions import LaunchArgument, YAMLFileSubstitution, YAMLReplaceSubstitution, YAMLMergeSubstitution, YAMLRetrieveSubstitution


def generate_launch_description():
    ss_root = FindPackageShare('arena_simulation_setup')
    pkg_nav2_bringup = FindPackageShare('nav2_bringup')
    robot = LaunchArgument('robot')
    namespace = LaunchArgument('namespace')
    frame = LaunchArgument('frame')
    use_sim_time = LaunchArgument('use_sim_time')
    global_planner = LaunchArgument('global_planner')
    local_planner = LaunchArgument('local_planner')
    inter_planner = LaunchArgument('inter_planner')

    substitutions = YAMLMergeSubstitution(
        YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'configs',
                'nav2',
                'model_params.yaml'
            ])
        ),
        YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'entities',
                'robots',
                robot.substitution,
                'model_params.yaml'
            ])
        ),
        # Load controller-specific configuration based on local_planner argument
        YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'configs',
                'nav2',
                'controllers',
                local_planner.substitution,
                'controller_config.yaml'
            ])
        ),
        # Load controller-specific configuration based on global_planner argument
        YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'configs',
                'nav2',
                'planners',
                global_planner.substitution,
                'planner_config.yaml'
            ])
        ),
        YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'configs',
                'nav2',
                'interplanners',
                inter_planner.substitution,
                'interplanner_config.yaml'
            ])
        ),
        YAMLFileSubstitution.from_dict(
            {
                'frame': frame.substitution,
                'namespace': namespace.substitution,
                'default_nav_to_pose_bt_xml': YAMLRetrieveSubstitution(
                    YAMLFileSubstitution(
                        PathJoinSubstitution([
                            ss_root,
                            'configs',
                            'nav2',
                            'interplanners',
                            inter_planner.substitution,
                            'interplanner_config.yaml'
                        ])
                    ),
                    'bt_navigator/ros__parameters/default_nav_to_pose_bt_xml'
                ),
                'default_nav_through_poses_bt_xml': YAMLRetrieveSubstitution(
                    YAMLFileSubstitution(
                        PathJoinSubstitution([
                            ss_root,
                            'configs',
                            'nav2',
                            'interplanners',
                            inter_planner.substitution,
                            'interplanner_config.yaml'
                        ])
                    ),
                    'bt_navigator/ros__parameters/default_nav_through_poses_bt_xml'
                ),
                'plugin_lib_names': YAMLRetrieveSubstitution(
                    YAMLFileSubstitution(
                        PathJoinSubstitution([
                            ss_root,
                            'configs',
                            'nav2',
                            'interplanners',
                            inter_planner.substitution,
                            'interplanner_config.yaml'
                        ])
                    ),
                    'bt_navigator/ros__parameters/plugin_lib_names'
                ),
            },
            substitute=True
        ),
    )

    substituted_parameters = YAMLReplaceSubstitution(
        obj=YAMLFileSubstitution(
            PathJoinSubstitution([
                ss_root,
                'configs',
                'nav2',
                'nav2.yaml'
            ])
        ),
        substitutions=YAMLFileSubstitution(substitutions)
    )

    robot_base_frame = YAMLRetrieveSubstitution(
        YAMLFileSubstitution(substitutions),
        os.path.join('robot_base_frame'),
    )

    robot_odom_frame = YAMLRetrieveSubstitution(
        YAMLFileSubstitution(substitutions),
        os.path.join('robot_odom_frame'),
    )

    remappings = [
        ('map_server', '/map_server'),
        ('/tf', '/tf'),
        ('/tf_static', '/tf_static'),
        ('map', '/map'),
    ]

    bringup_cmd_group = GroupAction([
        *(SetRemap(src=r[0], dst=r[1]) for r in remappings),
        Node(
            package='topic_tools',
            executable='relay',
            name='goal_pose_relay',
            arguments=['/goal_pose', 'goal_pose'],
        ),
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='map_broadcaster',
        #     arguments=['0', '0', '0', '0', '0', '0', 'world', 'map'],
        #     parameters=[{'use_sim_time': use_sim_time.substitution}]
        # ),
        # TF publishers
        # Node(
        #     package="tf2_ros",
        #     executable="static_transform_publisher",
        #     name="odomframe_to_baseframe_publisher",
        #     namespace=namespace.substitution,
        #     arguments=["0", "0", "0", "0", "0", "0", [frame.substitution, robot_odom_frame], [frame.substitution, robot_base_frame]],
        #     parameters=[use_sim_time.dict],
        # ),
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_node',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'odom0': PathJoinSubstitution(['/task_generator_node', frame.substitution, robot_odom_frame]),
                'odom0_config': [False, False, False, False, False, False, True, True, False, False, False, True, False, False, False],
                'imu0': PathJoinSubstitution(['/task_generator_node', frame.substitution, 'imu/data']),
                'imu0_config': [False, False, False, False, False, False, True, True, True, False, False, True, False, False, False],
                'odom_frame': PathJoinSubstitution([frame.substitution, robot_odom_frame]),
                'base_link_frame': PathJoinSubstitution([frame.substitution, robot_base_frame]),
                'world_frame': PathJoinSubstitution([frame.substitution, robot_odom_frame]),
                'map_frame': 'map',
                'publish_tf': True,
                "two_d_mode": True,
                "frequency": 30.0,
                "transform_time_offset": 0.0,
                "transform_timeout": 0.1,
            }],
        ),
        # AMCL Node
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            namespace=namespace.substitution,
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'global_frame_id': 'map',
                'odom_frame_id': PathJoinSubstitution([frame.substitution, 'odom']),
                'base_frame_id': PathJoinSubstitution([frame.substitution, 'base_link']),
                'scan_topic': PathJoinSubstitution(['/task_generator_node', frame.substitution, 'lidar']),
                'max_particles': 10000,
                'min_particles': 500,
                'initial_pose_received_timeout': 0.1,
                'recovery_alpha_slow': 0.001,
                'recovery_alpha_fast': 0.1,
                'set_initial_pose': True,
                'always_reset_on_initial_pose': True,
                # 'kld_err': 0.01,
                # 'kld_z': 0.90,
                # 'update_min_d': 0.05,
                # 'update_min_a': 0.05,
                # 'transform_tolerance': 0.5,
                'alpha1': 0.2,
                'alpha2': 0.2,
                'alpha3': 0.2,
                'alpha4': 0.2,
                'alpha5': 0.2,
                'beam_skip_distance': 0.5,
                'beam_skip_error_threshold': 0.9,
                'beam_skip_threshold': 0.3,
                'do_beamskip': True,
                'lambda_short': 0.1,
                'laser_likelihood_max_dist': 1.0,
                'laser_max_range': 100.0,
                'laser_min_range': -1.0,
                'laser_model_type': "likelihood_field",
                'max_beams': 120,
                'pf_err': 0.02,
                'pf_z': 0.99,
                'resample_interval': 1,
                'robot_model_type': "nav2_amcl::DifferentialMotionModel",
                'save_pose_rate': 0.5,
                'sigma_hit': 0.2,
                'tf_broadcast': True,
                'transform_tolerance': 0.2,
                'update_min_a': 0.1,
                'update_min_d': 0.1,
                'z_hit': 0.5,
                'z_max': 0.05,
                'z_rand': 0.5,
                'z_short': 0.05,
            }],
            remappings=[
                ('scan', PathJoinSubstitution(['/task_generator_node', frame.substitution, 'lidar'])),
                ('map', '/map'),
                ('initialpose', PathJoinSubstitution(['/task_generator_node', frame.substitution, 'initialpose'])),
            ]
        ),
        
        # Lifecycle Manager for AMCL
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'autostart': True},
                {'node_names': ["amcl", "planner_server", "controller_server", "smoother_server", "behavior_server", "bt_navigator"]},
                {'bond_timeout': 10.0},
                {'attempt_respawn_reconnection': True}
            ]
        ),
        # # Navigation Stack
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution(
                    [
                        pkg_nav2_bringup,
                        'launch',
                        'navigation_launch.py'
                    ]
                )
            ),
            launch_arguments={
                'use_sim_time': 'True',
                'local_planner': local_planner.substitution,
                'inter_planner': inter_planner.substitution,
                'autostart': 'True',
                'params_file': substituted_parameters,
                'use_composition': 'False',
            }.items()
        ),
    ])

    # Create the launch description and populate
    ld = LaunchDescription([
        robot,
        namespace,
        frame,
        use_sim_time,
        global_planner,
        local_planner,
        inter_planner,
        bringup_cmd_group,
    ])

    return ld
