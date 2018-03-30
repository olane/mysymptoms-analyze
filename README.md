# Extracting and analyzing data from the Android MySymptoms app

## Trying to get the data directly out of the app
### Get adb up and running

There's plenty of documentation on this so I won't repeat it. You'll need to enable developer options on your phone and enable the USB debugging option.

### Getting the app's package name

```
adb shell
pm list packages symptoms
```

This reveals the package name is `com.sglabs.mysymptoms`

### Trying to get the app data

I was going mostly off this blog post: https://blog.shvetsov.com/2013/02/access-android-app-data-without-root.html

Trying to get into the app's data directory didn't work because I wasn't root, and `su` didn't work because my phone isn't rooted.

I don't have an sd card in my phone so the second method was out.

Let's try the third method:

```
adb backup -f ~/data.ab -noapk com.sglabs.mysymptoms
```

Hm, this gives me the message 

```
Now unlock your device and confirm the backup operation.
```

But nothing is displayed on the phone. I suspect the app has `allowBackup:false`.

Running 

```
adb shell dumpsys package com.sglabs.mysymptoms | grep flags
```

confirms this - there's no `ALLOW_BACKUP` flag :(

```
adb shell dumpsys package com.sglabs.mysymptoms | grep dataDir
```

Reveals that `/data/user/0/com.sglabs.mysymptoms` is the data directory.

As expected, since we're not root, no dice with

```
adb pull /data/user/0/com.sglabs.mysymptoms
```

which just finds 0 files to pull.

There's a final method to try, which is to use `run-as com.sglabs.mysymptoms` to move the data somewhere we can get it. Unfortunately, because the application is not set as debuggable, this also fails. 

Curses!

## Having another look at the exports

### CSV

The csv export sounds useful, but it sucks. Here's a snippet:

```csv
12/26/2017, 10:00, Symptom, Stomach cramping, Intensity: 3, Duration: 6:00
12/26/2017, 10:55, Breakfast, "Porridge oats", "Cow's milk", "Chicken egg", "[ x 2 ]"
```
 It loses:
- All nesting information about which items are ingredients of other items
- Metadata such as which items have barcodes, are recipes, etc.
- It smushes quantities into the list of items for an event - you just have to know that if it's in square brackets, it's a quantity for the previous item. Sometimes quantities are formatted like `[ 200 mg ]` and sometimes like `[ x 2 ]`
- Symptom events (which might have multiple symptoms reported) again smush everything into a long list so for something like `Symptom, Nausea, Intensity: 1, Heartburn, Intensity: 1` you have to work out which intensity applies to which symptom.
- Exercise events seem to lose the intensity data altogether

### HTML

The HTML export exports the whole diary as a huge set of tables with inline styles, with `<br/>`s and `&nbsp;`es everywhere. Since it looks identical to the PDF report I assume they're using a HTML -> PDF library to create the PDFs and this export was just easy to add in once they'd done that. 

It does maintain more information than the CSV, although it does so at the cost of more difficult parsing. There's a table for each day, and two columns. The left column tells you the event type and the time (all smushed together with an image tag between them), and the right column is a `<br>` delimited list of stuff about the event. Here's a snippet:

```html
<table id="mhs-diary" summary="mySymptoms Diary"><colgroup><col class="mhs-diary-first" /></colgroup>
   <thead>
      <tr>
            <th scope="col">Tue 26 Dec 2017</th>
            <th scope="col"></th>
      </thead>
       <tbody>
      <tr bgcolor="fff5f5">
      <td width = "33%">10:00&nbsp<img class="symptom" />&nbspSymptom</td>
      <td width = "67%">Stomach cramping   (Intensity: 3 and Duration: 6 hrs 0 mins)</td>
   </tr>
   <tr bgcolor="ffffff">
      <td width = "33%">10:55 <img class="ingested" /> Breakfast</td>
      <td width = "67%">Porridge oats
      <br>Cow's milk
      <br>Chicken egg [ x 2 ]
      <br></td>
   </tr>
   ...
```

For a food event, the right hand column will be a list of food items. If the food item has ingredients those are listed in brackets. If an ingredient has ingredients, you get nested brackets. There's no HTML tag structure here - just a plain string. If an item has brackets in its name, well, you better be able to work out that the contents of those brackets aren't ingredients. If an item has a comma, there's a similar but even harder to solve problem.

I have an item like this:

```
Bread, brown (Wheat (Gluten)) 
```

To a parser, it's impossible to distinguish the two possibilities (one item called `Bread, brown` which contains `Wheat`, which contains `Gluten`; or one item called `Bread` followed by an item called `brown`, which contains `Wheat` which contains `Gluten`)

With this item:

```
Almond Milk (unsweetened, roasted) (Almonds) 
```

It actually _is_ possible to guess that the first set of brackets are part of the name of the thing, because if they were ingredients then the `(Almonds)` wouldn't make sense. Of course, if we're being really pedantic, you still can't be sure because the whole thing with both sets of brackets could be the name of one item. If the above item didn't specify `Almonds` as an ingredient it would be even harder to guess whether the words in the brackets were ingredients or not.

For exercise events, you get two lines, the first of which is the type of exercise and the second of which is attributes about that exercise:

```
Weights 
(Intensity: 6 and Duration: 0 hrs 45 mins)
```

I don't know if it's possible to have multiple exercise types in one event or more than those two attributes (all the events in my diary look roughly like this).

So:
- We still don't have all the metadata (recipes, barcodes etc.)
- We _do_ have ingredient hierarchy information, but it's impossible to parse in a bulletproof manner because the item names aren't quoted
- We have to traverse the HTML and filter out all the gubbins like break and image tags
- We still have the problem with quantities but at least it's unambiguously hacky to extract them (unless you have square brackets in your item names...)

### Combining the two

So the CSV is easy to parse but missing most of the information. The HTML is almost parseable but not quite. Luckily, between the two we actually do have enough information to have a good go at parsing the data.

Our problem with parsing the HTML strings was that the item names aren't quoted. However, in the CSV they _are_ - otherwise the CSV would probably end up malformed. When trying to parse a row from the HTML table, we can find the corresponding row in the CSV and get a list of the item names. We know the parser can't break apart those item names - they become tokens, and the parsing job becomes much simpler!

At this point, it's dinner time and I'm way too tired to start writing a parser.