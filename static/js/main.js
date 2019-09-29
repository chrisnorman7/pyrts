/* globals socketUrl, Sound, audio, gain, startAudio */
// Main script for the RTS.

let debug = false
let hotkeys = null
let authenticationSuccessful = false
let disconnecting = false
let reconnecting = false

// Below code to make Web Audio work on iOS modified from:
// https://paulbakaus.com/tutorials/html5/web-audio-on-ios/

let audioUnlocked = false

function unlockAudio() {
    if(!audioUnlocked) {
        // create empty buffer and play it
        let buffer = audio.createBuffer(1, 1, 22050)
        let source = audio.createBufferSource()
        source.buffer = buffer
        source.connect(audio.destination)
        source.start(0)
        // by checking the play state after some time, we know if we're really unlocked
        setTimeout(() => {
            if((source.playbackState === source.PLAYING_STATE || source.playbackState === source.FINISHED_STATE)) {
                audioUnlocked = true
            }
        }, 0)
    }
}

let menuIndex = null
let menuSearch = ""
let menuLastSearch = 0
let menuSearchInterval = 1000 // Milliseconds

const menuKeys = {}

function searchMenu(e) {
    e.preventDefault()
    let now = new Date().getTime()
    if (now - menuLastSearch >= menuSearchInterval) {
        menuSearch = ""
        menuIndex = 0
    }
    menuLastSearch = now
    menuSearch += e.key.toLowerCase()
    for (let i = menuIndex; i < menuEntries.length; i++) {
        let child = menuEntries[i]
        if (child.innerText.toLowerCase().startsWith(menuSearch)) {
            child.focus()
            menuIndex = i
            return
        }
    }
}

for (let char of "abcdefghijklmnopqrstuvwxyz1234567890 -='#/\\`[],.") {
    menuKeys[char] = searchMenu
}

const commands = {
    title: args => {
        document.title = args[0]
    },
    disconnecting: () => {
        disconnecting = true
    },
    hotkeys: args => {
        hotkeys = args[0]
    },
    message: args => {
        writeMessage(args[0])
    },
    menu: args => {
        let data = args[0]
        menu.hidden = false
        clearElement(menu)
        menuEntries.length = 0
        let h3 = document.createElement("h3")
        menu.appendChild(h3)
        makeSpeak(h3)
        h3.innerText = data.title
        if (data.dismissable) {
            let b = document.createElement("button")
            b.onclick = resetScreen
            menu.appendChild(b)
            makeSpeak(b)
            b.innerText = "Close"
        }
        let ul = document.createElement("ul")
        ul.role = "menu"
        menu.appendChild(ul)
        let focussed = false
        for (let item of data.items) {
            let li = document.createElement("li")
            ul.appendChild(li)
            li.role = "menuitem"
            li.tabIndex = 0
            menuEntries.push(li)
            li.onkeydown = (e) => {
                let key = e.key.toLowerCase()
                let index = menuEntries.indexOf(li)
                if (["arrowleft", "arrowup"].includes(key)) {
                    if (index) {
                        menuEntries[index - 1].focus()
                    }
                } else if (["arrowdown", "arrowright"].includes(key)) {
                    let next = menuEntries[index + 1]
                    if (next) {
                        next.focus()
                    }
                } else if (key == "home") {
                    menuEntries[0].focus()
                } else if (key == "end") {
                    menuEntries[menuEntries.length - 1].focus()
                } else if (data.dismissable && key == "escape") {
                    resetScreen()
                } else if (e.key == "Enter" && item.type == "item") {
                    li.click()
                } else {
                    let func = menuKeys[key]
                    if (func !== undefined) {
                        func(e)
                    }
                    return
                }
                e.preventDefault()
            }
            if (item.type == "item") {
                li.id = JSON.stringify({command: item.command, args: item.args})
                li.onclick = () => {
                    let data = JSON.parse(li.id)
                    soc.command(data.command, data.args)
                    resetScreen()
                }
                if (!focussed) {
                    focussed = true
                    li.focus()
                }
            } else {
                item.title = `- ${item.title} -`
            }
            li.innerText = item.title
        }
    },
    authenticated: () => {
        authenticationSuccessful = true
        loginForm.hidden = true
        keyboard.focus()
    },
    text: (args) => {
        let [label, command, argName, value, commandArgs] = args
        textCommand = command
        textArgName = argName
        textArgs = commandArgs
        textLabel.innerText = label
        textForm.hidden = false
        textText.value = value
        textText.focus()
        textText.select()
    },
    start_loop: (args) => {
        let url = args[0]
        let s = new Sound(url, true)
        loops.push(s)
        s.play()
    },
    stop_loops: () => {
        while (loops.length) {
            let loop = loops.pop()
            if (loop.source === null) {
                loop.stop = true
            } else {
                loop.source.stop()
            }
        }
    },
    sound: (args) => {
        let s = new Sound(args[0])
        s.play()
    },
    volume: args => {
        gain.gain.setValueAtTime(args[0], audio.currentTime)
    },
}

let soc = null
let connected = false
const loops = []
const messages = document.getElementById("messages")
const keyboard = document.getElementById("keyboard")
const menu = document.getElementById("menu")
const menuEntries = []
const textForm = document.getElementById("textForm")
const textLabel = document.getElementById("textLabel")
const textText = document.getElementById("textText")
let textArgName = null
let textCommand = null
let textArgs = null
const loginForm = document.getElementById("loginForm")
const username = document.getElementById("username")
const password = document.getElementById("password")
loginForm.onsubmit = e => {
    e.preventDefault()
    if (!username.value) {
        alert("Username cannot be blank.")
        username.focus()
    } else if (!password.value) {
        alert("Password canot be blank.")
        password.focus()
    } else {
        soc.command("authenticate", {username: username.value, password: password.value})
        if (audio == null) {
            startAudio()
        }
    }
}

textForm.onsubmit = e => {
    resetScreen()
    e.preventDefault()
    textArgs[textArgName] = textText.value
    textText.value = ""
    soc.command(textCommand, textArgs)
    // textArgs = null
    // textArgName = null
    // textCommand = null
}

window.onload = () => {
    window.AudioContext = window.AudioContext||window.webkitAudioContext
    menu.hidden = true
    textForm.hidden = true
    for (let button of document.getElementsByClassName("button")) {
        button.onclick = () => {
            unlockAudio()
            soc.command(button.id)
        }
    }
    createSocket()
    username.focus()
}

function makeSpeak(tag) {
    tag.setAttribute("aria-live", "polite")
    tag.setAttribute("aria-atomic", false)
}

function resetScreen() {
    textForm.hidden = true
    menu.hidden = true
    keyboard.focus()
}

function clearElement(e) {
    // A function to clear all children from an element.
    while (e.childElementCount) {
        e.removeChild(e.firstChild)
    }
}

function writeMessage(text) {
    let p = document.createElement("p")
    p.innerText = text
    p.tabIndex = 0
    messages.appendChild(p)
    window.scrollTo(0,document.body.scrollHeight)
}

function createSocket() {
    try {
        soc = new WebSocket(socketUrl)
    } catch(e) {
        writeMessage("*** Retrying failed connection. ***")
        return setTimeout(createSocket, 1000)
    }
    soc.onopen = () => {
        clearElement(messages)
        connected = true
        writeMessage("*** Connected ***")
        if (authenticationSuccessful) {
            soc.command("authenticate", {username: username.value, password: password.value})
        }
    }
    soc.onclose = () => {
        if (connected) {
            clearElement(messages)
            connected = false
            writeMessage("*** Disconnected ***")
            commands.stop_loops()
        }
        if (!disconnecting) {
            reconnecting = true
            setTimeout(createSocket, 1)
        }
    }
    soc.onmessage = (e) => {
        let data = JSON.parse(e.data)
        let command = commands[data.command]
        if (command) {
            command(data.args)
        } else {
            writeMessage(`Unknown command: ${data.command}.`)
        }
    }
    soc.onerror = () => {
        if (!reconnecting) {
            writeMessage("*** Connection failed. ***")
        }
    }
        soc.command = (name, args) => {
        if (!args) {
            args = {}
        }
        if (!connected) {
            writeMessage("You are not connected.")
        } else {
            soc.send(JSON.stringify({command: name, args: args}))
        }
    }
}

const possibleModifiers = {
    altKey: "alt",
    ctrlKey: "ctrl",
    shiftKey: "shift"
}

keyboard.onkeydown = (e) => {
    if (!connected) {
        return
    }
    let keys = []
    for (let name in possibleModifiers) {
        if (e[name]) {
            keys.push(possibleModifiers[name])
        }
    }
    if (e.key == "é") {
        key = ["alt", "ctrl", "e"]
    } else {
        keys.push(e.key)
    }
    let key = keys.join("+").toLowerCase()
    let command = hotkeys[key]
    if (command) {
        soc.command(command)
        e.stopPropagation()
        e.preventDefault()
    } else if (debug) {
        writeMessage(key)
    }
}
