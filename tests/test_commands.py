# from typer.testing import CliRunner

# from mgmt.app import app

# runner = CliRunner()


# def test_search():
#     with runner.isolated_filesystem():
#         # Create some test files
#         with open("file1.txt", "w") as f:
#             f.write("Test file 1")
#         with open("file2.txt", "w") as f:
#             f.write("Test file 2")

#         # Run the search command
#         result = runner.invoke(app, ["search", "file"])

#         # Assert the expected output or behavior
#         assert result.exit_code == 0
#         assert "total matches found" in result.output
#         # Add more assertions as needed
