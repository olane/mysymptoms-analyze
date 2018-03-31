# Getting data out of the sqlite database

## The tables

### The interesting ones
#### `flattened` 
This is a funny one. It just stores two columns - `ingestedparend_uuid` and `ingestedchild_uuid`. Some rows have the same UUID in both columns. It's clearly storing some sort of hierarchy - perhaps the ingredients-of hierarchy? The name of the table is quite perplexing if that's the case.

#### `ingested`
 Finally, data I recognise! Well, sort of. There's about 3.5k rows here, and a lot of columns. 
 
 There's clearly an entry for every food item in the app, and it looks like drinks, medications, stressors etc. are also mixed in. Each row has an `ingestedcategoryid` which joins onto the `ingestedcategory` table and tells you which of these it is.

 - The `isfactory` column is 1 if the item comes preloaded, 0 if it's user-added
 - The `frequency` and `iscommonallergen` columns are always 0 and seem unused
 - `isitem` is 0 if the item is a recipe and 1 if it isn't
 - `numberofingestedevents` counts how many times the item has been used
 - `usage` is a confusing one - it's an int that is usually 0 but sometimes in the thousands. Perhaps it's a measure of how many times that item is used over all the app's users, but that data isn't available for all items?
 - `barcode` and `creationdate` and `ingredientcount` and `isincloud` and `deleted` are fairly self explanatory
 - `clean` is always 0 - don't know what that is
 - `baseitem` looks like it stores the "Kind of" - it's either null, or it's a uuid that refers to another ingested row.

 There's a text field called `ingredientnames` which has the string representation of the ingredients list - for example, my `Clementine & almond cake` entry has `Almonds, Chicken egg, Clementines, Sugar` in this field. Note that it doesn't contain sub-ingredients, so the full hierarchy must come from somewhere else.

#### `ingesteddetail`
This links ingested events (see below) to ingested items, attaching a bit of extra info like serving size. There's a column called `quantity` which is always null and I assume is vestigial. The actual serving size is stored in a column called `fquantity` (which is an int, or if the row has no quantity information is -1), combined with `servingsizeuuid` which points to the `servingsize` table and tells you whether the quantity is in grams, mg, slices, etc.

There's a significant number of rows in here with no `ingested_uuid`. Instead, they have a `duration` and `intensity` (for rows with an `ingested_uuid` those two columns are `-1`). These rows appear to be used to attach duration/intensity information to events. It really looks like these should be in a separate table. It actually looks like _every_ ingested event has one of these, even food/drink events where they're not recorded in the app (in this case duration and intensity are both 0).

#### `ingestedevent`

This is what's created when you actually add an entry to your diary. It basically just has an id (uuid), a time and some notes. There's also a reference to what type of `ingestedeventtype` it is, a last modified date, whether it's been synced or not and whether it's been deleted. This table is... pretty sensible :D

#### `ingestedtoingested`

This is quite similar to `flattened`. It maps a `ingestedparentuuid` to a `ingestedchilduuid`. It also has a quantity, represented the same was as in `ingesteddetail` with an int and a reference to the `servingssize` table. Finally, there's a user id.

#### `reactioneventtype`
These are all the types of "outcome" (I have 30 in my db). For example: Nausea, Headache, Bowel Movement, Gas, etc.

Flags:
- `isarchived` this is true for items I've deleted
- `isdeleted` this matches `isarchived` for me
- `isselected` true for one item, not sure of the meaning
- `issymptom` false for reactions that are shown as their own event, such as Energy, Sleep quality, and Bowel movement. True for symptoms, which are shown together in the "symptom" UI.
- `lastanalysis` true for the last symptom that was analysed, I think
- `syncstatus` whether it's been synced, presumably

Other:
- `reportcount` number of times this reaction is in the diary
- `lastmodified` timestamp
- `quantitymeasure` always null

There seem to be two copies of each outcome, for me. One of the two copies has no user id, no sync status and no last modified date. Weird.

#### `scores`
This is clearly the analysis results. There's a lot of floats in here that look like they're measuring various scores, confidence ratings, correlations etc.

I'm not going to go into this too much right now.

### The slightly interesting ones
- `brand` contains all of the brands I've got in the app (both ones I've added and the ones preloaded into the app). You just get a name, a country code, whether the brand is a restaurant (I haven't seen this used within the app and it's `0` for all my entries, maybe it's vestigial).
- `classification` contains 10 rows with things like Dairy, Fruits, Grains etc. I recognise these from the app - they appear as defaults under some items' "Kind of" field. However, it's possibly to put any other type of food item in that field, too, so it's a little confusing that these are separated out.
- `favourites` is a bit more meaty, finally - 562 rows. It stores, for various event types, my "favourite" (read: most used) ingested items, along with a total count for each item in that category. Possibly it actually stores all of the item/category pairs in order to keep track of those counts, but I'd have to investigate more to work that out.
- `ingestedcategory` this is a prepopulated table of the categories of "ingested" items - (Drinks, Foods, Medications, Stressors, Exercises, Other, Environment, and Supplements)
- `ingestedchanges` I think this is a list of edited items. It maps a column called `uuid` to a column called `ingested_uuid`, which is clear as mud, but my hunch is that `uuid` points to a new item and `ingested_uuid` points to the old version of that item. There's a flag called `hidden` which in my database is always true.
- `ingestedeventtype` similar to `ingestedcategory` but for event types (Breakfast, Snack, etc)
- `ingestedtype` this has one row in it for "Stress". I'm not sure why.
- `ingestedtoingestedtype` this maps an `ingested` row to an `ingestedtype`, as you might expect. I only have one row in mine, though, which maps to the stress item in `ingestedtype`.
- `servingsize` this stores all the types of serving size in the app (grams, millilitres, teaspoons, etc.). Each one has lots of properties. This table seems pretty well thought out (which actually shines through in the app - dealing with quantities works pretty seamlessly, although I tend not to bother entering them because I'm lazy)
- `userret` it looks like this maps reaction event types to their last analysis

### The really boring ones
- `analysisconfig` appears to be something to do with what settings for analyses that have been performed. I've only got 9 rows in mine so I'm not sure if it only stores recent analyses or if these are just the configs and are re-used by analysis jobs
- `analytics` appears to store analytics about when a user has viewed certain pages. Mine is empty, although I haven't turned off sharing app usage data. Perhaps it's removed from here after it's uploaded, or perhaps it's filtered out of the database snapshot sent for debugging.
- `android_metadata` just has a single row, with a single column, and stores my phone's locale (`en_GB`)
- `appconfig` again has a single row and stores app settings such as whether I've accepted the terms and conditions, and an `appdataversion` which is presumably a database version number
- `chart` is empty but has three columns - `ingested_uuid`, `symptom_intervals` and `ingestedevent_counts`. My hunch is it's used to cache data used for generating charts.
- `exportconfig` just has one row with a start date and an end date. Must be something to do with exporting to csv/html.
- `imagetoevent` looks like it's meant to store a mapping from event to images but it's empty
- `ingestedtogroup` another empty table
- `languages` one row, "English", with enabled = 1
- `sqlite_sequence` built in table for auto ids

## Data integrity issues

- Almost all columns use `-1` to mean "there's no value", even if they aren't int columns (some UUID columns do this!). I'd much rather have nulls (or, ideally, normalisation to avoid nulls altogether)
- `ingested.ingredientnames` might have the string `"null"` rather than the value `<null>`. This looks like a bug (and I have seen this pop up as text in the ingredients of some items in the app, in certain views)
- All bools are stored as ints with 0 being false and 1 being true. There's nothing stopping you putting something silly like 7 in one of these fields.
- All dates appear to be stored as unix timestamps in int fields, with 0 being used instead of null.
- Some, but not all, tables have their own id column (usually a UUID stored as TEXT) but still use the default sqlite `_id` column as their primary key.
- Very few columns are marked as `NOT NULL` despite most of them looking like they shouldn't be nullable.
- There's various tables that could do with normalization to reduce the number of nulls (or -1s) needed
- Some of the naming is pretty confusing
- There's some columns which aren't used any more which are presumably vestigial but could be cleaned up to prevent confusion



## Let's write some queries

### Trying to get the ingredient hierarchy

#### using `flattened`
```sql
SELECT 
	parent.name,
	parent.uuid,
	parent.ingredientnames,
	child.uuid,
	child.name
FROM main."ingested" as parent
LEFT JOIN flattened ON flattened.ingestedparent_uuid = parent.uuid
LEFT JOIN ingested as child ON child.uuid = flattened.ingestedchild_uuid
WHERE parent."name" like '%Almond milk%';
```

Hm, this sort of works, but there's a lot of weirdness. For one thing, there's a lot of duplicates in `flattened`. Also, lots of things map to themselves, which doesn't make much sense. It seems to do _transitive_ relationships - if an item A contains an ingredient B which in turn contains an ingredient C, you get an entry in `flattened` linking A->C (as well as A->B and B->C).

Note that this does track "Kind of" relationships as well as ingredients.

My hunch: this is used as an easy way to make the flattened list of ingredients for things like the CSV export. Just left join an item onto all its children, remove any duplicate names, and print them out. No recursion necessary. 

Possibly this is also a performance optimisation - in older versions of SQLite there's no way to do a recursive query so you'd have to do the recursion in the calling code, possibly generating many SQL queries in a loop. By doing the recursion ahead of time and storing the result in `flattened`, it might reduce the time taken to render of a whole list of items significantly.

#### Let's try `ingestedtoingested`

```sql
SELECT 
	parent.name,
	parent.uuid,
	parent.ingredientnames,
	child.uuid,
	child.name,
	ingestedtoingested._id,
	ingestedtoingested.user
FROM main."ingested" as parent
 JOIN ingestedtoingested ON ingestedtoingested.ingestedparentuuid = parent.uuid
 JOIN ingested as child ON child.uuid = ingestedtoingested.ingestedchilduuid
WHERE parent."name" like '%Almond milk%';
```

This works a bit better - we've lost the transitivity so we just get the direct children. One thing to note is that we've also lost the "Kind of" data here - presumably we'll need another query to get that if we want it.

Annoyingly, we still get duplicates. It looks like all the entries in the `ingestedtoingested` table are duplicated, one entry with a user id and one entry without. In fact, there's also duplicates where the user column is identical, so even omitting null/non-null user ids won't work. This may be the underlying reason that `flattened` has lots of duplication in it.

Amending the query to return distinct items gives us the correct results, but it's a bit annoying to have to use `SELECT DISTINCT`:

```sql
SELECT DISTINCT
	parent.name,
	parent.uuid,
	parent.ingredientnames,
	child.uuid,
	child.name
FROM main."ingested" as parent
 JOIN ingestedtoingested ON ingestedtoingested.ingestedparentuuid = parent.uuid
 JOIN ingested as child ON child.uuid = ingestedtoingested.ingestedchilduuid
WHERE parent."name" like '%Almond milk%';
```

