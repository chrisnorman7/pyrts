# PyRTS
A web-based realtime strategy game.

## Running the server
* Install Python (version 3.7.4 or later is bound to work).
* Install the requirements from requirements.txt.
* Run the main.py file.
* Access the running server over HTTP, on port 7873 of your server.

## Playing the game
When you first connect you will be presented with the main menu. If you are the first connected player, you will automatically be made an admin.

### Starting a game
When you have selected a map, either by creating a new map, letting the computer create you a practise map, or by joining someone else's map, you must usually wait for other players to join your map. This is not the case with practise maps, as you will be the only player.

When the game has started properly, you can begin to build, recruit, exploit, and fight.

### Movement
There are a few different ways of moving around the map.

* Arrow keys move you north (up arrow), east (right arrow), south (down arrow), or west (left arrow).
* The J key allows you to select an item on the map to jump to.
* The g key allows you to type some coordinates to jump to.

### Objects
There are 3 types of units you will interract with in a game. Each has its different uses.

#### Features
Features are feature of the land that you might look at in real life. By default, mines, quarries, lakes, forests, and fields are all present.

Each object contains a certain resource, which can be exploited (harvested) by units, and stored in buildings.

Once resources have been taken by a unit and put into a building, they can be spent to build more buildings, or recruit more units.

#### Units
A unit is a worker, or thing you can move around. By default, some of the more common types of unit are peasants and farmers.

Each unit has its own skill set. It may know how to build buildings, it may know how to exploit resources, or it may know how to fight. They can also move about the map. They can guard, heal, and patrol.

Some units know how to fight, and they will defend themselves if they are attacked. Others don't, and they just stand there and hope someone else comes to their aid.

If a unit gets injured in a fight, you will need to heal it with a unit that can heal other units, to prevent it dying in the next attack.

While guarding, certain units can automatically heal other units who are injured in their presence, and some will automatically repair damaged buildings they see.

#### Buildings
Buildings store resources and act as homes for units. A unit will only take resources to its home, and a building must contain the right amount of resources to recruit more units, or for one of its occupants to build another building.

You can change a unit's home at any time, and this is advantageous if you want to redirect resources.

Buildings also have some more esoteric uses, like being way points for transports (which you probably won't see straight away), and some may not have any use at all beyond being a super difficult place for anyone to take away from you, or being able to recruit a unique unit type.

### Playing a game
#### Hotkeys
There are lots of keyboard shortcuts which can be used to play the game (61 at time of writing), and it is futile to try to list them all here. Here are a few of the common ones:

* Get help with shift + slash (/). That's like typing a question mark on most keyboards.
* Show the menu (activate) the thing you just selected with the space key.
* Switch back and forth between objects at your current coordinates with comma (,) and full stop (.).
* Select objects at your current coordinates by number with the number keys 1 to 9 on the top row. The 0 key reminds yu of the currently-selected object.
* Select and deselect units with the x key. Deselect all units with shift + x (more useful than you might think).
* Select entire groups of units with the qwerty keys (q, w, e, r, t, y, u, i, o, and p). Add shift to select individual units from a menu. The A key acts on all units you control.
* Access the main menu with the f1 key.

### Doing stuff.
Let's imagine you start a game. You've got one town hall and nothing else. What to do?

First you want to recruit a peasant. You focus the town hall with the number 1 key, and you hit space to bring up the menu.

The first item there is "Recruit Peasant", so you hit enter.

You wait four seconds, until your new friendly peasant announces their arrival.

Next, you want it to build you a farm, because you've got your eye on world domination and stuff.

You select the peasant with the number 2 key, because objects are ordered by their type (buildings, then features, and finally units), and then by the order in which they appear on the map.

You press space again, because you really want the menu. The first entry is for building a town hall, but you know that's for muppets, and you, my friend, are far from being a muppet. You pick the second option, bravely named "Build Farm".

A new farm is built so quickly, you are shocked by the efficiency of your little worker. Just to check it you press the 2 key again. Don't forget that objects are ordered by type, and because farms are buildings, they will always appear before lowly peasants.

Pressing the h key tells you that the farm's health is 0 out of a possible maximum of 30. If it were a human, it would be bleeding all over your nice new strip of land. Time for some repairs.

You hit the space key, and there it is, repair is right at the top of the menu. You press enter, and are told that you must first select a unit... And it was all going so well.

Because repairs can be performed by multiple units simultaneously, the repair command is one of those commands that requires you to select one or more units first. You can do that a couple of ways. You can move through all the units at your current location with the comma (x) and full stop (.) keys, hitting x whenever you want to add a unit to the selection, or you can use the qwertyuiop keys to select all units of a particular type.

Because you only have one unit thus far, you take option 3, and hit a. This yields the helpful text: "1 unit selected".

Hitting space again (because the farm is still the focussed object) brings up the activation menu for buildings. Repair is still right at the top, so you hit enter.

The one solitary unit you have under your tyranical control gets to work, banging and clattering their way to farm-house bliss.

Finally, your helpful little peasant tells you that they have completed the repairs you're not actually paying them to do, and you're in business. Because you're the type that likes to build universities, which (as everyone knos) are built exclusively by farmers, but can themselves recruit a panoply of useful units, you set about recruiting a farmer.

As before, you press space (because your farm is still selected), and find the "Recruit Farmer" option. It does almost nothing, apart from to tell you about the resources you don't have, because this is a new farm, and your peasant is a lazy sort, and hasn't included them in the base design.

Because your farm is still selected, you press the z key, which tells you what resources something contains. The z key tells you that the server is not in point of fact trolling you, and the farm is truly resource free.

Time to do some exploiting!

You're pretty sure the town hall has some resources left over from your very frugal recruitment drive earlier, and just to check, you hit the 1 key (because the town hall is a building, and furthermore it's the first building you were given, so it's the first object to appear on this square. The z key tells you there's buckets of stuff left over, and you reckon it would be pretty sweet if you could just move stuff around, like you can in the real world!

How astute! You can do just that. Like land features, buildings contain resources, namely the ones yours (or someone else's) units put there. The only difference is that any unit can exploit any resources from a building. If the unit and the building are not owned by the same player, units must resort to stealing. That's a whole different matter, and one you can experiment with on your devious little own.

Just to speed up the work some, you find your town hall by hitting 1, and recruit a few more peasants, by hitting the space key to bring up the menu, and hitting enter on "Recruit Peasant". When you've got 5 or so, you can begin the real work.

Because you want to get into good habbits, you abandon the a key (which stands for all units) in favour of the q key. Because peasants are the first type of unit you recruited, the q key selects all of them in your employ.

Because you want the resources moved to your farm, you select your farm again (with the 2 key), and find the "Set Home" option. You are informed that a number of homes have been updated, and your units are effectively rehoused.

Now you switch back to the town hall (with the 1 key), hit space, and choose the "Exploit" option. You are presented with a list of all the resource types that can possibly be contained by a building, and you choose the first one in the list that you were given when attempting to recruit a farmer.

Your peasants dutifully pootle off and start relocating resources from the town hall to the farm. You switch back to the farm with the 2 key, and keep attempting to recruit a farmer to see what other resources are needed. When the list shrinks, you go back to the town hall with the 1 key, and exploit again, this time selecting a different resource type for your peasants to remove to your farm.

Eventually you don't get a list, you just get told to wait, and a new farmer is recruited. You complete this process until you have a couple of farmers at your disposal.

Because you've actually got friends, you're not alone on this map, and you reckon you have a chance, if you're quick. You take control of all your farmers with the w key (because they're the second type of unit you've recruited), and you head out to join your pal with the j key.

When you're there, you find your friend presiding over 2 farms. You summon your farmers by pressing space, and choosing the "summon" option. After what seems like an age, they appear, and you can get down to the real business of destruction. You could have summoned your peasants too, but peasants are a funny lot, and they don't know how to attack each other, let alone destroy an enemy's building.

You press the 1 key, because up to this point you've been lead to believe that buildings always appear first. Turns out that the "getting started" guide for the game didn't give you the full story, and players actually appear first. You hurridly press the 2 key, and are rewarded by the positive selection of your friend's first farm.

In the menu you find the "Destroy" option, and you press enter. Your farmers talk a big game, and it sounds as though they know what they're talking about. They smash and crash until a great cheer goes up, and your friend has one less farm to worry about. You quickly dispatch the second farm as well, then it's off to find the town hall.

You move with the arrow keys until you find the town hall, and select it with the one key. Farmers are summoned, and the destroy order is given from the ubiquitous menu, and your friends fledgling town hall goes the same way as farms 1 and 2.

You win the game because your mate has no buildings or units left, you've both learnt some valuable lessons about the game, and this guide ushers itself out with a flourish.

### For admins
As an administrator, you can use the same space menu on players to set and unset their admin bit, disconnect them from the server, and delete their character.

You also have access to the "m" menu for editing the types that make the game run.

As a bonus, you can also hit the backspace key to execute pure Python code.