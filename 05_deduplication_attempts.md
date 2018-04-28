# We still have data problems

Despite all our scrubbing, we still have a lot of duplicate items - 155 items have non-unique names. In fact, one of my items (Butter) has 6 different entries. And that's just counting exact matches, without taking into account capitalization, formatting, spelling and other inconsistencies.

## Approach 1: merge the database items

I started trying to massage the database to fix these issues, but quickly ran into problems. Items don't exist in a vacuum - they're in a tree structure. If two duplicates have a `baseitem` that's the same, that's fine, but what if the're different? Does one of them win? Do you merge the `baseitem`s too?

You have the same problem with ingredients, although you can just merge the lists which isn't too bad. Things like `creationdate` and `barcode` are also problems, but that's data we care less about so we can probably just pick a winner.

You also have to make sure everything that references the merged items has its reference properly updated to point to the new merged item. This is harder than it sounds when the database is lacking a lot of integrity contraints, because it's hard to know if you've missed anything.

This could all be overcome, but it's a lot of work!

## Approach 2: let's leave this until later

This approach requires significantly less effort, so was an instant frontrunner. Let's focus on the visualization for now, and we can worry about deduplication at a later point in the pipeline. I think it's likely that our analysis won't be dealing with the tree structure too much later on (since stats and graphs normally operate on lists of numbers and suchforth), and once the data is into that format it will probably be much easier to merge things appropriately (lists are easier to merge than trees).

If this doesn't work out we can always come back to approach 1.