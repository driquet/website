---
title: "Excuses to Listen: How Audiobooks Rebuilt My Routine"
date: 2026-10-09T09:00:00+02:00
tags: ["audiobooks", "books", "litrpg", "habits", "running"]
showTableOfContents: true
---

{{< lead >}}
These days, when I pick my next book, I check its length first. Ten hours? Not long enough. I want twenty, thirty, ideally a series with a dozen volumes I can chain without thinking about what comes next.
{{< /lead >}}

This is new for me. My relationship with reading has always been a series of highs and lows. Some months I would not open a single book. Other months I would stay up way too late for "one more chapter", pay for it the next morning, and do it again that night. Then the streak would break, and the book would sit on my nightstand for weeks.

Two years ago, I started listening to audiobooks. The streak never broke. More than that: listening quietly pulled a bunch of other habits along with it, including one I never thought I would have.

## How it started: a lonely astronaut and a desert planet

My first two audiobooks were *Project Hail Mary* and *Dune*, on my French Audible account.

*Project Hail Mary* was the revelation. Ray Porter does not just read the book; he performs it. Some parts of that story simply work better with your ears than with your eyes, and if you have listened to it, you know which ones.

*Dune* was a different kind of revelation. I had tried to read it before and struggled. In audio, it just flowed. And *Dune* is also the book that got me running, but I will come back to that.

## LitRPG: a video game you read

Then I discovered a genre I did not know existed: LitRPG. The short version: the characters live in a world ruled by game mechanics. They have stats, levels, skills, and a "System" that pops notifications in their heads ("You have reached level 12!"). It sounds silly, and sometimes it is, on purpose. It is also incredibly addictive, because progression is visible and constant, and the series are *long*.

My gateway was *Dungeon Crawler Carl*. Then came *He Who Fights with Monsters* (12 books in about four months) and *The Primal Hunter* (14 books in about nine months). That is when I understood I was not reading in bursts anymore. I was just... always reading.

## Excuses to listen

Here is the trick: an audiobook needs a moment where your hands and eyes are busy but your brain is not. So I started creating those moments. Every one of them became an excuse to listen.

### Running and walking

Running for the sake of running never made sense to me. Going in circles, alone, with nothing but my own breathing for company? No thanks. What I needed was a distraction, and *Dune* was it. I put on my headphones, went out, and suddenly the run was just the thing my legs were doing while my head was on Arrakis.

It did not stay a distraction for long. The order flipped.

{{< lead >}}
> I used to need a book to run. Now I run to get to the book.
{{< /lead >}}

Walking followed the same path, and it became an even stronger habit. I now take a walk every day, for no other reason than to listen. No destination, no step goal: just a chapter or two, and I come back home with fresh air in my lungs and the story a little further along.

### Bedtime

Before audiobooks, my evenings ended on my phone, scrolling until my eyes gave up. Now, I put on a book, turn off the lights, and listen until I am sleepy enough.

It did not always go smoothly. More than once, I fell asleep mid-chapter and woke up with no idea what had happened, so I had to restart the chapter the next day. A small price: no screen before bed, and I sleep better than I used to.

### English

I only listen in English. I even had to create an Audible account in another country to access the English catalogue. Hundreds of hours of native speakers, accents, and made-up fantasy vocabulary later, my English comprehension is noticeably better. Free bonus.

### Everything else

Cooking, cleaning the house, the gym, driving. Chores I used to postpone are now twenty more minutes of the story, and I almost look forward to them. Even long flights changed: they are no longer hours to kill, they are an entire book.

## The numbers

Audible tells me I have listened to **969 hours** on that account, and that is not counting *Project Hail Mary* and *Dune*. Call it a thousand hours. That is roughly 24 full work weeks, or about 1.6 hours a day, every day, for twenty months.

Here is where those hours went, using Audible's runtime for every book in my history:

{{< chart >}}
type: 'bar',
data: {
  labels: ['The Primal Hunter', 'He Who Fights with Monsters', 'Dungeon Crawler Carl', 'Mistborn (in progress)', 'Harry Potter (full cast)', 'Bobiverse', 'Others'],
  datasets: [{
    label: 'Hours',
    data: [277, 270, 159, 81, 50, 29, 51],
    backgroundColor: ['#f97316', '#f97316', '#f97316', '#3b82f6', '#3b82f6', '#3b82f6', '#94a3b8'],
    borderRadius: 6,
  }]
},
options: {
  indexAxis: 'y',
  plugins: { legend: { display: false } },
  scales: {
    x: {
      title: { display: true, text: 'Hours listened', color: document.documentElement.classList.contains('dark') ? 'rgb(203, 213, 225)' : 'rgb(51, 65, 85)' },
      ticks: { color: document.documentElement.classList.contains('dark') ? 'rgb(203, 213, 225)' : 'rgb(51, 65, 85)' },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : 'rgba(100, 116, 139, 0.2)' }
    },
    y: {
      ticks: { color: document.documentElement.classList.contains('dark') ? 'rgb(203, 213, 225)' : 'rgb(51, 65, 85)' },
      grid: { display: false }
    }
  }
}
{{< /chart >}}

Three LitRPG series alone account for more than 700 hours.

Those thousand hours are the whole point. It does not come from motivation or discipline. I never decided to "read more". I just attached listening to things I was already doing, and to a few new ones, until it became the default. It is the same idea I wrote about in [my New Year resolutions post]({{< ref "posts/new-year-resolutions" >}}): build a system that keeps running on its own, instead of relying on a burst of motivation that fades.

## Recommendations

If you want to try, here is where I would start.

### The audio showcases

Books where the narration is half the experience.

{{< book cover="covers/hail-mary.jpg" title="Project Hail Mary" author="Andy Weir" narrator="Ray Porter" length="16h" url="https://www.audible.com/pd/B08G9PRS1K" >}}
What an audio experience. Ray Porter does not read this book, he performs it. If you only try one audiobook, make it this one.
{{< /book >}}

{{< book cover="covers/dcc.jpg" title="Dungeon Crawler Carl" author="Matt Dinniman" narrator="Jeff Hays" length="8 books · ~160h" url="https://www.audible.com/pd/B08V8B2CGV" >}}
My first LitRPG. A man, his ex-girlfriend's cat, and a sadistic alien game show. Hilarious, surprisingly dark, with strong characters, and Jeff Hays voices the entire cast.
{{< /book >}}

{{< book cover="covers/bobiverse.jpg" title="The Bobiverse" author="Dennis E. Taylor" narrator="Ray Porter" length="6 books · ~64h" url="https://www.audible.com/pd/B01L082HJ2" >}}
A software engineer wakes up as a space probe that can clone itself. Nerdy, funny, and the natural next step after *Project Hail Mary*: same narrator.
{{< /book >}}

### Long hero progressions

The comfort food: a hero starts weak, gets stronger, and you get to watch every step of it for hundreds of hours.

{{< book cover="covers/hwfwm.jpg" title="He Who Fights with Monsters" author="Shirtaloon (Travis Deverell)" narrator="Heath Miller" length="13 books · ~290h" url="https://www.audible.com/pd/1774248182" >}}
An office-supplies store manager gets dropped into a world of magic and monsters, and refuses to take any of it seriously. Heath Miller nails the humor.
{{< /book >}}

{{< book cover="covers/primal-hunter.jpg" title="The Primal Hunter" author="Zogarth" narrator="Travis Baldree" length="15 books · ~300h" url="https://www.audible.com/pd/B09MWP4277" >}}
Earth gets integrated into a multiverse run by a System, and an office worker discovers he is a natural-born hunter. Pure, steady power progression.
{{< /book >}}

## What's next: back to fantasy

After two years of LitRPG, I am taking a break and going back to classic fantasy. Right now, I am finishing Brandon Sanderson's *Mistborn* (narrated by Michael Kramer), and I love it. It reminds me of Robin Hobb's *Farseer Trilogy*, which I loved when I was younger: a young outsider, a secret mentor, a hidden magic, and a court full of people who want you dead. The good news: Sanderson's Cosmere is huge, so the "not long enough" problem is solved for a while.

Next on the list: *Red Rising*. Time to go for a run.
