# OxChief Troubleshooting: "My robot won't come online"

You set everything up, started the OxChief software, but your robot still shows
**offline** on the website. Take a breath — this is almost always **one small
thing** being slightly off, not anything broken. This guide walks you through
finding it, one step at a time. You don't need to know anything about robots,
autopilots, or GPS to follow along.

> Throughout this guide we assume your Pi's username is `pi`, so paths start with
> `/home/pi/`. If you used a different username when you set up the Pi, just swap
> it in — e.g. `/home/yourname/src/oxchief/`.

---

## First — what does "online" actually mean?

A small program (we call it **the client**) runs on the Raspberry Pi inside your
autopilot box. That program "phones home" to oxchief.com over the internet. When
that call connects, your robot turns **online** on the website.

For that to happen, four things have to be true:

1. **The Pi has power and the client is running.**
2. **Your `.oxchief` file is in the right place.** Think of this file as your
   robot's password — it proves the robot is yours.
3. **The Pi has internet.**
4. **Your flight controller is plugged in and powered on.** The "flight
   controller" is the **Cube** — the box that actually steers and drives the
   mower. The client waits for it before going online.

Good news: you do **not** need GPS or RTK (super-accurate GPS) working to come
online. If GPS isn't set up yet, your robot will *still* show online — you can
deal with GPS afterward.

---

## Step 1 — Update to the latest version (this fixes a known cause)

Older versions could get "stuck" during startup if a GPS device wasn't attached.
The latest version fixes that, so **update first** — it's quick and often solves
the problem by itself:

```
cd /home/pi/src/oxchief/oxchief-client
git pull
sudo ./re.sh
```

Wait about a minute, then refresh the website and check again.

---

## Step 2 — Read the logs (they almost always tell you what's wrong)

The client constantly prints what it's doing. Watch it with:

```
cd /home/pi/src/oxchief/oxchief-client
./logs.sh
```

(Press **Ctrl-C** to stop watching — that won't stop the robot, just the
log viewer.)

Now look at the bottom of what scrolls by. **Is one line repeating over and over?**
That repeating line is your clue. Find it in the list below and follow that
section.

If it says *"No running Docker containers found,"* the client isn't running at
all — jump to **"The client isn't running"** near the bottom.

---

## Match what you saw to one of these

### A) "auth file ... not found", or the client stops a second after you start it

This is the **most common** problem. Your `.oxchief` file (the robot's password)
is missing or in the wrong folder. You'll see a line like:

```
Error: OxChief auth file (/home/pi/src/oxchief/.oxchief) not found. Please login to OxChief to get the contents of this file.
```

The file must sit **one level above** the `oxchief-client` folder — here:

```
/home/pi/src/oxchief/.oxchief
```

The classic mistake is putting it *inside* the `oxchief-client` folder. Check
where it actually is:

```
ls -la /home/pi/src/oxchief/.oxchief
```

- If you see the file listed, good — it's in the right place.
- If you see *"No such file or directory,"* it's missing or misplaced.
  Re-download it from oxchief.com (**Settings → click your robot → "Download
  .oxchief client file"**) and save it to exactly the path above.

Then start again with `sudo ./re.sh`.

> Keep your `.oxchief` file private — it's your robot's password. Don't paste its
> contents to anyone.

### B) "Found 0 of 2 flight-controller telem ports ..." (repeating)

The Pi can't find the two USB connections to your flight controller (the Cube).
In plain terms: the cables between the Pi and the Cube aren't both plugged in, or
the Cube isn't powered.

- Make sure the Cube is powered on.
- Make sure **both** flight-controller USB adapters are firmly plugged into the
  Pi (these are the little adapters labeled `_OxTelem1` and `_OxTelem2`).
- If you're not sure, unplug and replug them.

You don't have to restart — the moment both are connected, the client continues
on its own. (Running `sudo ./re.sh` again is also fine.)

### C) "No MAVLink heartbeat from flight controller ..." (repeating)

The Pi found the USB connections, but the flight controller isn't answering back.
Usually that means the Cube isn't powered, or a cable to it is loose.

- Confirm the Cube is powered and its lights are on.
- Check the cable between the Cube and its USB adapter.

Like the previous one, it connects on its own once the Cube starts responding.

### D) "u-blox receiver not found, searching again..." (repeating) — this one is fine!

**This line is not why you're offline.** It just means no GPS-corrections device
is attached, which is OK — your robot comes online without it. You can ignore
this line for now and set up GPS/RTK later.

If this is the **only** repeating line and your robot is *still* offline, you're
likely on an older version that got stuck here — do **Step 1** (update) above and
it'll go away.

### E) It comes online as the wrong robot, or still offline after everything above

Each robot has its own `.oxchief` file. If you grabbed the wrong one, the Pi
"logs in" as a different robot. You can safely check which robot your file is for:

```
grep robot_id /home/pi/src/oxchief/.oxchief
```

Make sure that number matches the robot you're watching on the website. If it
doesn't, download the correct robot's `.oxchief` file and replace it.

---

## The client isn't running

If `./logs.sh` says *"No running Docker containers found,"* the client isn't up.
Start it:

```
cd /home/pi/src/oxchief/oxchief-client
sudo ./re.sh
```

Watch what it prints. If it stops with the "auth file not found" message, go to
section **(A)** above.

---

## Is the Pi actually on the internet?

The Pi has to reach the internet to come online. Test it:

```
ping -c 3 oxchief.com
```

You want to see replies come back (it should say something like "0% packet
loss"). If nothing comes back, the Pi isn't online — fix its internet connection
(usually the phone hotspot it connects through) and try again.

---

## Still stuck? Here's exactly what to send us

Post on the [OxChief subreddit](https://www.reddit.com/r/OxChief/) (or email
support) and include:

1. What's running:
   ```
   docker ps
   ```
2. The recent logs — run `./logs.sh`, let it print for about 10 seconds, press
   **Ctrl-C**, and copy everything it showed.

> **Never share the contents of your `.oxchief` file** — it's your robot's
> password. If we ask, the only line that's safe to share is the one that starts
> with `robot_id=`.

---

## Quick command reference

| What you want | Command |
|---|---|
| Update + restart the client | `cd /home/pi/src/oxchief/oxchief-client && git pull && sudo ./re.sh` |
| Watch the logs | `./logs.sh`  (press Ctrl-C to stop) |
| Is the client running? | `docker ps` |
| Where's my password file? | `ls -la /home/pi/src/oxchief/.oxchief` |
| Is the Pi online? | `ping -c 3 oxchief.com` |

Full setup instructions live in the
[OxChief Mower Client Setup](OXCHIEF_MOWER_CLIENT_SETUP.md) guide.
