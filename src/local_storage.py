"""
Author: Wayne Baswell

Handles persistent storage
"""
import sqlite3
import json
import robot_state

class LocalStorage:
    """
    Class for managing local storage (via SQLLite database) operations.
    """

    def __init__(self):
        self.setup_local_database()

    def setup_local_database(self) -> None:
        """
        Create local SQLLite database.
        """
        #local (sqlite) database connection
        self.connection = sqlite3.connect("oxchief.db")
        #local (sqlite) database cursor
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self) -> bool:
        """
        Create local tables
        """
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS mavlink_forward_ip(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, ip TEXT)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS missions(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, value TEXT, description TEXT)")
            self.connection.commit()
        except sqlite3.Error as error:
            print("Failed to create SQLLite db tables ", error)
            return False
        return True

    def save_mission_info_to_db(self) -> bool:
        """
        Save mission waypoint info
        """
        try:
            #clear out existing missions data
            self.cursor.execute("DELETE FROM missions")
            #get waypoint data as string
            waypoints_in_autopilot_string = json.dumps(robot_state.waypoints_in_autopilot)
            waypoints_in_mission_string = json.dumps(robot_state.waypoints_in_mission)
            #save data to db
            self.cursor.execute("INSERT INTO missions(name, value) VALUES(?,?)", ('waypoints_in_autopilot', waypoints_in_autopilot_string))
            self.cursor.execute("INSERT INTO missions(name, value) VALUES(?,?)", ('waypoints_in_mission', waypoints_in_mission_string))
            self.cursor.execute("INSERT INTO missions(name, value) VALUES(?,?)", ('last_autopilot_loaded_waypoint_number_end', str(robot_state.last_autopilot_loaded_waypoint_number_end)))
            self.cursor.execute("INSERT INTO missions(name, value) VALUES(?,?)", ('last_autopilot_loaded_waypoint_number_start', str(robot_state.last_autopilot_loaded_waypoint_number_start)))
            self.connection.commit()
        except sqlite3.Error as error:
            print("Failed to insert missions data into SQLLite table", error)
            return False
        return True

    def load_mission_info_from_db(self) -> bool:
        """
        Load mission waypoint info in db into robot_state
        """
        try:
            self.cursor.execute("SELECT value FROM missions WHERE name='waypoints_in_autopilot'")
            rows = self.cursor.fetchall()

            for row in rows:
                waypoints_in_autopilot_string = row[0]
                robot_state.waypoints_in_autopilot = json.loads(waypoints_in_autopilot_string)

            self.cursor.execute("SELECT value FROM missions WHERE name='waypoints_in_mission'")
            rows = self.cursor.fetchall()

            for row in rows:
                waypoints_in_mission_string = row[0]
                robot_state.waypoints_in_mission = json.loads(waypoints_in_mission_string)

            self.cursor.execute("SELECT value FROM missions WHERE name='last_autopilot_loaded_waypoint_number_end'")
            rows = self.cursor.fetchall()

            for row in rows:
                last_autopilot_loaded_waypoint_number_end_string = row[0]
                robot_state.last_autopilot_loaded_waypoint_number_end = int(last_autopilot_loaded_waypoint_number_end_string)

            self.cursor.execute("SELECT value FROM missions WHERE name='last_autopilot_loaded_waypoint_number_start'")
            rows = self.cursor.fetchall()

            for row in rows:
                last_autopilot_loaded_waypoint_number_start_string = row[0]
                robot_state.last_autopilot_loaded_waypoint_number_start = int(last_autopilot_loaded_waypoint_number_start_string)

        except sqlite3.Error as error:
            print("Failed to loading missions data from local db", error)
            return False
        return True
