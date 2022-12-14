# Rose
Rose is a "Relationship Evaluation Algorithm". It's not a dating app, or anything like that. It simply evaluates a current or potential relationship based on an objective standard.

## Installing
Rose is built on PyQt6
```
git clone https://github.com/smartycope/Rose.git
cd Rose
pip install -r requirements.txt
python3 src/main.py
```

## How it Works
You start out with a set of questions that relate to a relationship i.e. *Are they tall*, *Do they treat you well*, *Do you like them*, etc. There's a set of boilerplate questions if you don't want to make your own from scratch. You can also add questions as you please.

First you go through all the questions and ask yourself, "how important is it to me that ________" (*they are tall*, *they treat you well*, *you like them*). That creates a preferences file which you can save and reuse as you like. You only have to do this once, but as you learn more, you might go through and change your preferences. You can also specify certain things as "dealbreakers", but be careful of having too many.

Then, you go through all the questions again with a specific person in mind, i.e. *is John tall*, *does John treat me well*, *do I like John*, etc. This gives you an evaluation file, which you can save for funsies.

Finally, you need to specify a "*pickiness*" value. This is just a number between 0 and 1 that says how desperate you are.

The program then essentially takes a weighted average (how important the quality is to you * how much the specific person fulfills the quality) of all the questions, and if it's greater than your pickiness value, then you should enter a relationship with them, if not, don't. Or, alternately, whether you should end the relationship with them or not.

### File Types
There are 2 types of files:
- *.pref preference files, where you set what your preferences are in general
- *.eval files, where it saves your evaluation on a specific person

## *PLEASE NOTE*
This is solely a method of objectively quantifying your feelings based on previous standards *you yourself* set. It is not the end-all be-all of deciding whether to enter or end a relationship with someone. It is simply a way to know how you yourself are feeling, when it's difficult to be objective. That's why it's called Rose, it's meant to help you take off the "rose-colored glasses" and see things clearly, and to help you not change your standards when presented with something new you think you like. However, it's only as good as the standards you set. If you have crappy standards, it's going to tell you to enter crappy relationships. I recommend calibrating the preferences file **before** you are considering entering or exiting a relationship, so it will be more objective.

*I take no responsibility if my algorithm somehow ruined your relationship*
