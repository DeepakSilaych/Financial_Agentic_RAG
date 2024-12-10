import sqlite3
from sqlite3 import Error
from typing import List, Dict, Set


class FinancialDatabase:
    def __init__(self, db_file: str = "financial_reports.db"):
        self.db_file = db_file
        self.initialize_database()

    def create_connection(self):
        """Create a database connection to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(f"Error while connecting to database: {e}")
            return None

    def create_table(self, conn):
        """Create the financial reports table."""
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sqlite (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    year TEXT,
                    quarter TEXT,
                    type TEXT,
                    topics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
            print("Table created successfully")
        except Error as e:
            print(f"Error while creating table: {e}")

    def initialize_database(self):
        """Initialize the database and create required tables."""
        conn = self.create_connection()
        if conn is not None:
            # self.create_table(conn)
            conn.close()
        else:
            print("Error! Cannot create the database connection.")

    def reset_database(self):
        """Reset the database by dropping the table and recreating it."""
        conn = self.create_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS sqlite")  # Drop the existing table
            conn.commit()
            self.create_table(conn)  # Recreate the table
            print("Database reset successfully")
            return True
        except Error as e:
            print(f"Error resetting database: {e}")
            return False
        finally:
            conn.close()

    def insert_report(self, report_data: Dict) -> bool:
        """
        Insert a new financial report into the database.

        Args:
            report_data (dict): Dictionary containing report data with keys:
                - company_name (str | None)
                - year (str | None)
                - quarter (str | None)
                - type (str)
                - topics (set of strings | None)

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        conn = self.create_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sqlite 
                (company_name, year, quarter, type, topics)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    report_data.get(
                        "company_name", ""
                    ),  # Default to empty string if None
                    report_data.get("year", ""),  # Default to empty string if None
                    report_data.get("quarter", ""),  # Default to empty string if None
                    report_data.get("type", ""),
                    (
                        ",".join(report_data.get("topics", []))
                        if report_data.get("topics")
                        else ""
                    ),  # Default to empty string if None
                ),
            )
            conn.commit()
            return True
        except Error as e:
            print(f"Error inserting report: {e}")
            return False
        finally:
            conn.close()

    def get_reports_by_company(self, company_name: str) -> List[Dict]:
        """Retrieve all reports for a specific company."""
        conn = self.create_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM sqlite 
                WHERE company_name = ?
                ORDER BY year DESC, quarter DESC
            """,
                (company_name,),
            )

            columns = [description[0] for description in cursor.description]
            reports = []
            for row in cursor.fetchall():
                report = dict(zip(columns, row))
                # Handle null topics by converting empty strings back to empty set
                if report.get("topics"):
                    report["topics"] = set(report["topics"].split(","))
                else:
                    report["topics"] = set()
                reports.append(report)
            return reports
        except Error as e:
            print(f"Error retrieving reports: {e}")
            return []
        finally:
            conn.close()

    def get_reports_by_year(self, year: str) -> List[Dict]:
        """Retrieve all reports for a specific year."""
        conn = self.create_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM sqlite 
                WHERE year = ?
                ORDER BY company_name, quarter
            """,
                (year,),
            )

            columns = [description[0] for description in cursor.description]
            reports = []
            for row in cursor.fetchall():
                report = dict(zip(columns, row))
                if report.get("topics"):
                    report["topics"] = set(report["topics"].split(","))
                else:
                    report["topics"] = set()
                reports.append(report)
            return reports
        except Error as e:
            print(f"Error retrieving reports: {e}")
            return []
        finally:
            conn.close()

    def get_companies(self) -> Set[str]:
        """Retrieve all distinct company names."""
        conn = self.create_connection()
        if not conn:
            return set()

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT company_name FROM sqlite")
            companies = {row[0] for row in cursor.fetchall()}
            return companies
        except Error as e:
            print(f"Error retrieving companies: {e}")
            return set()
        finally:
            conn.close()

    def get_all_reports(self) -> List[Dict]:
        """
        Retrieve all reports in the database.

        Returns:
            List[Dict]: A list of dictionaries where each dictionary represents a report.
        """
        conn = self.create_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sqlite ORDER BY company_name, year, quarter")

            # Get column names for dictionary keys
            columns = [description[0] for description in cursor.description]
            reports = []
            for row in cursor.fetchall():
                report = dict(zip(columns, row))
                # Convert topics back to a set
                if report.get("topics"):
                    report["topics"] = set(report["topics"].split(","))
                else:
                    report["topics"] = set()
                reports.append(report)
            return reports
        except Error as e:
            print(f"Error retrieving all reports: {e}")
            return []
        finally:
            conn.close()

    def get_union_of_topics(self, metadata: Dict, global_set: Set[str]) -> Set[str]:
        """
        Get the union of all topics from the database based on the provided metadata filters.

        Args:
            metadata (dict): A dictionary containing 'company_name' and 'year' for filtering.
            global_set (set): A global set of topics to return if no filters are applied.

        Returns:
            set: A set of unique topics based on the applied filters.
        """
        # If both company_name and year are None in metadata, return the global set of topics
        if not metadata.get("company_name") and not metadata.get("year"):
            return global_set

        # Initialize an empty set to collect topics
        topics_set = set()

        # If company_name is provided, filter by company_name
        if metadata.get("company_name"):
            reports = self.get_reports_by_company(metadata["company_name"])
        # If year is provided, filter by year
        elif metadata.get("year"):
            reports = self.get_reports_by_year(metadata["year"])
        else:
            # Retrieve all reports if no filters are applied
            reports = self.get_all_reports()

        # Loop through the reports and collect topics
        for report in reports:
            if report.get("topics"):
                # Add topics from the current report to the topics set
                topics_set.update(report["topics"])

        return topics_set

    def get_all_company_year_pairs(self) -> List[Dict]:
        """
        Retrieve all company-year pairs from the database.

        Returns:
            List[Dict]: A list of dictionaries where each dictionary contains a company name and its corresponding year.
        """
        conn = self.create_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            # Query to select company_name and year columns
            cursor.execute(
                "SELECT company_name, year FROM sqlite ORDER BY company_name, year"
            )

            company_year_pairs = []
            for row in cursor.fetchall():
                company_name, year = row  # Unpack the tuple
                company_year_pairs.append(
                    {
                        "company_name": company_name,
                        "filing_year": year,  # We use "filing_year" as the field for year in the dictionary
                    }
                )

            return company_year_pairs

        except Error as e:
            print(f"Error retrieving company-year pairs: {e}")
            return []
        finally:
            conn.close()


# Initialize the database
# db = FinancialDatabase()

# # db.reset_database()

# # report = {
# #     'company_name': None,
# #     'year': None,
# #     'quarter': None,
# #     'type': 'Annual Report',
# #     'topics': {'revenue', 'profits', 'growth'}
# # }
# # db.insert_report(report)

# report = {
#     'company_name': 'Apple Inc',
#     'year': '2023',
#     'quarter': 'Q1',
#     'type': 'Annual Report',
#     'topics': {'revenue', 'profits', 'growth'}
# }
# db.insert_report(report)

# report = {
#     'company_name': 'Alphabet Inc',
#     'year': '2023',
#     'quarter': 'Q1',
#     'type': 'Annual Report',
#     'topics': {'revenue', 'profits', 'growth'}
# }
# db.insert_report(report)

# report = {
#     'company_name': 'Meta Inc.',
#     'year': '2023',
#     'quarter': 'Q1',
#     'type': 'Annual Report',
#     'topics': {'revenue', 'profits', 'growth'}
# }
# db.insert_report(report)

# report = {
#     'company_name': 'Meta Inc.',
#     'year': '2023',
#     'quarter': 'Q1',
#     'type': 'Annual Report',
#     'topics': {'revenue', 'profits', 'growth'}
# }
# db.insert_report(report)

# report = {
#     'company_name': 'Apple Inc',
#     'year': '2023',
#     'quarter': 'Q2',
#     'type': 'Quarterly Report',
#     'topics': {'revenue', 'profits', 'growth'}
# }
# db.insert_report(report)

# # check all the functions

# # Get all reports for Apple Inc
# apple_reports = db.get_reports_by_company('Apple Inc')
# for report in apple_reports:
#     print(f"Year: {report['year']}, Topics: {report['topics']}")

# # Get all reports from 2023
# reports_2023 = db.get_reports_by_year('2023')
# for report in reports_2023:
#     print(f"Company: {report['company_name']}, Topics: {report['topics']}")

# # Get all distinct companies
# companies = db.get_companies()
# print("Companies:", companies)


"""
How to use this database:
  
1. Initialize the database:
    from database import FinancialDatabase
    db = FinancialDatabase()

2. Insert a new report:
    report = {
        'company_name': 'Apple Inc',
        'year': '2023',
        'quarter': 'Q1',
        'type': 'Annual Report',
        'topics': {'revenue', 'profits', 'growth'}
    }
    db.insert_report(report)

3. Query reports by company:
    # Get all reports for Apple Inc
    apple_reports = db.get_reports_by_company('Apple Inc')
    for report in apple_reports:
        print(f"Year: {report['year']}, Topics: {report['topics']}")

4. Query reports by year:
    # Get all reports from 2023
    reports_2023 = db.get_reports_by_year('2023')
    for report in reports_2023:
        print(f"Company: {report['company_name']}, Topics: {report['topics']}")

5. Get all distinct companies:
    companies = db.get_companies()
    print("Companies:", companies)

Database Schema:
---------------
Table: sqlite
Columns:
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- company_name: TEXT
- year: TEXT
- quarter: TEXT
- type: TEXT
- topics: TEXT (comma-separated values)
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Notes:
- The `topics` field is stored as a comma-separated string in the database but converted to a `set` in Python.
- Null fields (like `topics`) are gracefully handled with defaults (e.g., empty set).
"""
