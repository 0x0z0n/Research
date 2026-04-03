### Step 1: Create the Table and Mapping via KQL

Cancel out of that "Get Data" wizard for a second and go to your main query window in ADX. Run these two commands one after the other. 

**1. Create the empty table:**
```kusto
.create table RawEventLogs (TimeGenerated: datetime, EventID: string, Computer: string, RawEvent: dynamic)
```

**2. Create the JSON ingestion mapping:**
This tells ADX exactly how to match the JSON keys in your local file to the columns we just made.
```kusto
.create table RawEventLogs ingestion json mapping 'EventLogMapping' 
'['
'  {"column":"TimeGenerated", "Properties":{"path":"$.TimeGenerated"}},'
'  {"column":"EventID", "Properties":{"path":"$.EventID"}},'
'  {"column":"Computer", "Properties":{"path":"$.Computer"}},'
'  {"column":"RawEvent", "Properties":{"path":"$.RawEvent"}}'
']'
```

### Step 2: Upload the File into the Existing Table

Now that ADX knows exactly what the data looks like, it won't try to guess (and fail). 

1. Go back to **Get Data** -> **Local file**.
2. **Destination tab:** Instead of creating a new table, choose **Existing table** and select `RawEventLogs`.
3. Upload your `Security.jsonl` file.
4. **Inspect tab:** Because you selected an existing table, you will now see an option for **Mapping**. 
5. Select **Existing mapping** and choose `EventLogMapping` from the dropdown. 
6. The format error will disappear, and you can click **Finish**.

