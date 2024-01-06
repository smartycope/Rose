# Rose
Rose is a "Relationship Evaluation Algorithm". It is **not** a dating app, or anything like that. It simply evaluates a current or potential relationship based on an objective standard that you yourself set beforehand.


## Installation
Rose is built on PyQt6
```bash
git clone https://github.com/smartycope/Rose.git
cd Rose
pip install -r requirements.txt
python src
```


## Explanation & Instructions
You start out with a set of questions that relate to a relationship i.e. *Do they treat you well*, *Are they tall*, *Do you like them*, etc. There's a set of boilerplate questions if you don't want to make your own from scratch. Just press the `Restore Defaults` button. You can also add questions as you please.

First, go through all the questions and ask yourself, "how important is it to me that ________" (*they are tall*, *they treat you well*, *you like them*). That creates a preferences file which you can save and reuse as you like. You only have to do this once, but as you learn more, you might go through and change your preferences. You can also specify certain things as "dealbreakers", but be careful of having too many.

Then, you go through all the questions again with a specific person in mind, i.e. *is John tall*, *does John treat me well*, *do I like John*, etc. This gives you an evaluation file, which you can save for funsies.

Finally, you need to specify a "*pickiness*" value. This is just a number between 0 and 1 that says how desperate you are. 0 being "*I will date anyone as long as they breathe*" and 1 being "*They have to fit every aspect **perfectly** in order for me to date them*

The program then essentially takes a weighted average (how important the quality is to you * how much the specific person fulfills the quality) of all the questions, and if it's greater than your pickiness value, then you should enter a relationship with them, if not, don't. Or, alternately, whether you should end the relationship with them or not.


## File Types
There are 2 types of files:
- *.pref preference files, where you set what your preferences are in general
    - The intent is that this is filled out before you meet someone, so that your liking someone doesn't effect your decision
- *.eval files, where it saves your evaluation on a specific person


## *PLEASE NOTE*
This is solely a method of objectively quantifying your feelings based on previous standards *you yourself* set. It is not the end-all be-all of deciding whether to enter or end a relationship with someone. It is simply a way to know how you yourself are feeling, when it's difficult to be objective. That's why it's called Rose, it's meant to help you take off the "rose-colored glasses" and see things clearly, and to help you not change your standards when presented with someone new you think you like. However, it's only as good as the standards you set. If you have crappy standards, it's going to tell you to enter crappy relationships. I recommend calibrating the preferences file **before** you are considering entering or exiting a relationship, so it will be more objective.

*I take no responsibility if my algorithm somehow ruins your relationship. This is meant to provide information, and is not meant to be the final decision on a relationship. I am not a therapist.*

*This algorithm correctly predicted I should date the woman who is now my wife, so it seems to work*
