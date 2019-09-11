let audio = null
let gain = null
window.AudioContext = window.AudioContext || window.webkitAudioContext

function startAudio() {
    audio = new AudioContext()
    gain = audio.createGain()
    gain.connect(audio.destination)
}

const buffers = {}

class Sound {
    constructor(url, loop) {
        this.source = null
        this.stop = false
        this.url = url
        if (loop === undefined) {
            loop = false
        }
        this.loop = loop
    }

    getBuffer() {
        let xhr = new XMLHttpRequest()
        xhr.open("GET", this.url)
        xhr.responseType = "arraybuffer"
        xhr.onload = () => audio.decodeAudioData(xhr.response).then((buffer) => this.playBuffer(buffer))
        xhr.send()
    }
    
    playBuffer(buffer) {
        buffers[this.url] = buffer
        if (!this.stop) {
            let source = audio.createBufferSource()
            this.source = source
            source.loop = this.loop
            source.buffer = buffer
            source.connect(gain)
            source.start(0)
        }
    }
    
    play() {
        let buffer = buffers[this.url]
        if (buffer === undefined) {
            this.getBuffer()
        } else {
            this.playBuffer(buffer)
        }
    }
}

this.startAudio = startAudio
this.Sound = Sound
