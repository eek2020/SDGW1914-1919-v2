
# Initial Help

I have an mdb file that I need to get the data from, I understand this is possibly MS Access but I have a mac so how do I get the data?

15:53

Identified Mac compatibility challenge and formulated extraction strategy

Good news — there are several ways to get data out of an .mdb file on a Mac without needing Microsoft Access:

MDB Viewer (Mac App) The easiest option is probably "MDB/ACCDB Viewer" from the Mac App Store. It's a lightweight app that lets you open Access databases, browse tables, and export to CSV. There are a few versions available, some free and some paid.

MDB Tools (Command Line) If you're comfortable in the terminal, mdb-tools is an open-source package you can install via Homebrew:

bash
brew install mdb-tools
Then you can list tables and export them:

bash
mdb-tables yourfile.mdb          # list all tables
mdb-export yourfile.mdb TableName > output.csv   # export a table to CSV

This is a great option given your comfort with the command line and vibe coding approach — quick and scriptable.

- DB Browser for SQLite (with conversion) You could convert the .mdb to SQLite first using mdb-tools, then open it in DB Browser for SQLite (free, Mac-native). This gives you a nice GUI to explore and query the data.
- LibreOffice Base LibreOffice (free) includes a database module that can open .mdb files, though it can be a bit clunky for this purpose.

---

Here's a quick workflow:
bash# Install
brew install mdb-tools

## See what you're working with

mdb-tables -1 yourfile.mdb

## That'll list one table per line — then export whichever ones you need

mdb-export yourfile.mdb "TableName" > TableName.csv
If there are lots of tables and you want to dump everything at once:
bash# Export all tables to individual CSVs
for table in $(mdb-tables -1 yourfile.mdb); do
    mdb-export yourfile.mdb "$table" > "${table}.csv"
    echo "Exported: $table"
done
If you want to get a sense of the schema first (column names, types, relationships):
bashmdb-schema yourfile.mdb
Once you've got CSVs, you can open them in Excel, Numbers, or pull them into Python/Power BI — whatever works for your workflow. If any of the tables are massive and you only need a subset, you could pipe through head or load into a SQLite database for querying.
Give it a go and shout if you hit any snags.
