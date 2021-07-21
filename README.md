# Bot_Discord

This Bot using the Python Discord API can be used to play music but also throw most types of dice rolls for tabletop RPGs such as DnD, Vampire the Masquarade or Warhammer.
Can take requests from multiples servers at the same time and handle a queue for each.
Also store the songs on a database to reduce loading time if it has been listened to before on any other server the bot is in.

Use the prefix "?" before the differents commands in order to call the bot.

?roll [x]d[y] will roll x number of dice of the y size.
You can add other specifications after the [x]d[y] to the command in order to change how does the throw will work:
- > [z]: will determine how many of those dice roll and superior to the Z number
- < [z]: same but for inferior to Z 
- + or - [Z] will add or substract Z to every dice result
- adv or disadv will throw an other dice for every dice thrown initially 
- exp will make the dice explode and throw another dice for every minimal or maximal result
- add will make the sum of every dice thrown

?play youtube URL (and also playlist) will make the bot play the audio of the video(s) linked to the command or add it to the queue is something is already playing.

?leave will make the bot leave the channel of the user

?pause will make the bot pause the current song

?resume will make the bot resume the paused song

?skip will make the bot skip the current song and start the next one on the queue

The bot will also display the song title and it's duration when starting.
