# Log Distributor MVP for Resolve AI (Submission by Vishwa Sheth)

Hi there 👋 This project is a self-contained demo of a high-throughput log pipline.
The pipeline includes:
* **Emitters** that generate a JSON log packet at up to 10 requests/second each.
* A single **Distributor** that load-balances packets to **Analyzers** using *smooth weighted round-robin*, 
has live health probes, and dynamic weight-rebalance.
* A **React dashboard** showing real-time metrics, lets you pause/resume emitters, enable/disable analyzers,
and streams the routed packets.

### **Quick Setup Guide Videos**
If you want to get things running, I've created two quick videos to walk you through how to do that:
- Installation and setup guide: [https://youtu.be/D99SrfNL6q4](https://youtu.be/D99SrfNL6q4)
- How to add/remove Emitters and Analyzers: [https://youtu.be/9bGvrmHtGic](https://youtu.be/9bGvrmHtGic)

## Table of Contents

* [Why Python](#why-python-)
* [Assumptions](#assumptions-)
* [Features](#features-)
* [Distributor Design](#distributor-design-️)
* [Data Model](#data-model-)
* [API](#api-)
* [Setup, Install & Run](#setup-install--run-)
* [Improvements/Future Work](#improvementsfuture-work-)

## Why Python? 🐍

You'll notice this project's backend is written entirely in Python. The emitter, distributor, and analyzer
services are all containerized in Docker but the builds are from Python files. The reason for this is 
because:
1. Python is the tool I'm most comfortable with and I can get my hands dirty the quickest in without
needing to ramp up on most technical details. 
2. For demo purposes, a familiar language helped me spin up instances of each service pretty quickly 
and, most importantly, it gave me the opportunity to learn the core working principles of each service 
well since I had to create them from scratch.
3. Implementing multithreaded behaviour in Python is quite straightforward with `asyncio`, and locking
asynchronous routines is as straightforward as `with self._lock`. Encapsulating code that alters state 
variables with this one line ensures thread safety.

---

## Assumptions 💭

Before starting this project, I made a couple important assumptions that weren't explicitly explained
in the project description. I'll state them here for your reference.

1. It doesn't matter which Emitter's packets go to which Analyzer.
2. Each packet has equal priority and should be sent in order of timestamp (chronological order).
3. The number of Emitters is fixed at build time, the number of Analyzers can increase or decrease.
4. Users will be able to view only the 500 most recent logs sent to Analyzers since this is stored
on disk and I don't have infinite memory.
5. Emitter request rate will be between 0 and 10 requests per second to simulate high throughput.
6. Existing Analyzers and Emitters can be taken offline and brought back online during runtime.
7. The Distributor has a FIFO queue where messages are enqueued and then dequeued. The queue has a maximum
capacity of 10k packets. The queue should only ever start filling up if all Analyzers are offline.
8. Should there be packets waiting in queue that have not been sent to an Analyzer, all messages in the queue
will be sent to the same Analyzer once available.

---

## Features ⚙️

Here are all the features that I have implemented in this project. Unless explicitly stated, all features
are functional.

- have N log Emitters
- have M Analyzers
- have one Distributor
- data packet sent as a JSON (refer to Data Model section)

Log Emitter:
- able to generate and send packets
- able to tune request rate (reqs/sec) from **0 to 10**
- able to be paused (to simulate shutdown) but not lose generated packets
- able to be paused when no Analyzers available
- queue up to 5000 outgoing packets if no Analyzers available or if Emitter is paused (because of limited memory)

Analyzer:
- able to receive packets
- able to be turned off (to simulate shutdown) and brought back up

Distributor:
- able to asynchronously receive multiple packets via POST request
- able to assign weights to each analyzer (total to 1.0)
- able to readjust weights if one or more Analyzers goes down or comes back up while maintaining relative weights
- able to send payloads to Analyzers in priority of weight (if weights are not assigned, assume equal priority)
- able to delete existing Analyzers
- able to add new Analyzers (❌ this feature does not work properly ❌)

UI:
- able to adjust each Emitter's request rate
- able to pause/unpause an Emitter (simulating shutdown)
- able to pause/unpause an Analyzer (simulating shutdown)
- able to delete Analyzer
- able to add new Analyzer (❌ this feature does not work properly ❌)
- view past 500 recent logs sent to Analyzers

---

## Distributor Design 🏛️

The Distributor is comprised of five components.

```markdown
{Emitters} --> Queue --> Registry --> [ Dispatcher, Health Monitor, Metrics/Logging WebSocket ]
                                             |
                                             |
                                             v
                                        {Analyzers}
```

**Queue:** A simple FIFO queue, helps separate I/O from distribution logic. Intakes packets from N Emitters via POST requests.

**Registry:** Keeps list of M Analyzers, their health status, weights, effective weights. Handles re-weighting when 
analyzers go down or come up, and handles choosing which Analyzers to send packets to.

**Dispatcher:** Pops packets from Queue and calls on Registry to choose Analyzer. Uses Smooth Weighted Round Robin (SWRR) 
to pick analyzers.

**Metrics/Logging WebSocket:** Allows pinging for component metrics and past 500 logs.

---

## Data Model 📊

Below is the data packet that each Emitter will send.

```python
packet = {
            "packetId": uuid,
            "emitter": emitter ID,
            "messages": [
                {
                    "ts": UTC datetime,
                    "level": "INFO",
                    "service": "demo_service",
                    "host": emitter ID,
                    "message": "Sample log message from {emitter ID}",
                }
            ]
        }
```

---

## API 🛜

All routes are hosted on `http://localhost:8000` (Distributor container) and proxied to the Distributor, Emitters, and/or Analyzers as needed.

| Path | Method | Body | Description |
| :---- | :------ | :----- | -----------: |
| `/log-packet` | `POST` | `packet` (refer to Data Model section) | Emitter pushes packet via this endpoint |
| `/registry` | `GET` | N/A | Lists Analyzers available to Distributor |
| `/analyzer/{aid}/enable` | `POST` | N/A | Enable an Analyzer `aid` that was disabled |
| `/analyzer/{aid}/disable` | `POST` | N/A | Disable an Analyzer `aid` that is enabled |
| `/registry/add` | `POST` | `{ "id": string, "url": string, "weight": float }` | Add new Analyzer to list of available Analyzers (❌ this feature does not work properly ❌) |
| `/registry/{aid}` | `DELETE` | N/A | Delete an Analyzer `aid` from the Distributor's registry |
| `/emitter/{eid}/pause` | `POST` | N/A | Pause Emitter `eid` |
| `/emitter/{eid}/resume` | `POST` | N/A | Resume/un-pause Emitter `eid` | 
| `/emitter/{eid}/rate` | `POST` | `{ "rps": float }` | Set Emitter `eid` request rate to a number between 0 and 10 (inclusive) |
| `/emitter/{eid}/metrics` | `GET` | N/A | Fetch metrics for Emitter `eid` (buffer length, rps, paused status) |

| WebSockets | Description |
| :--------- | ----------: |
| `/ws/metrics` | WebSocket for getting Emitter, Analyzer, and Distributor metrics at 1 Hz (look at `payload` in `distributor/app/main.py -> ws_metrics(ws)`) |
| `/ws/logs` | WebSocket for getting list of recent logs without requiring to parse through each Analyzer |

---

## Setup, Install & Run 🏃

This is a fully self-contained project so setup and installation is all done in one easy step.

1. Clone this repo locally
2. Navigate to project root
3. Install all dependencies on backend and front-end, build, and run (this will all be done when running `docker compose build`)
4. Access the UI on `http://localhost:8000`

```bash
git clone git@github.com:VishwaSheth03/log-distributor-demo.git
cd log-distributor-demo
docker compose build; docker compose up
```

Configure the number of Emitters, Analyzers, request rate of Emitters, and weight of Analyzers is all controlled from `docker-compose.yml`.
Here you can add as many Emitter and Analyzer containers as you like.

To add an Analyzer simply add:
```docker
analyzerX:
    build: ./analyzers
    expose: ["9000"]
```
in the list of existing Analyzer containers, ensuring `analyzerX` is a unique Analyzer name. Also, you will have to add its JSON config
into the `ANALYZERS_JSON` list at the top. The format for a new Analyzer's config is `{ "id": string, "url": "http://analyzerX:9000/ingest","weight": float }`. Ensure that the `id` is unique and the `url` matches the `analyzerX` container name.

To add an Emitter simply add:
```docker
emitterY:
    build: ./emitters
    environment:
      - DISTRIBUTOR_URL=http://distributor:8000/log-packet
      - EMITTER_ID=emitY
      - RATE_RPS=number
    expose: ["9100"]
    depends_on: [distributor]
```
in the list of existing Emitter containers, ensuring `emitterY` is a unique Emitter name. Note that the `RATE_RPS` should be between 0 and 10 (inclusive). Also, you will have to add its JSON config into the `EMITTERS_JSON` list at the top. The format for a new Emitter's config is `{ "emitter_id": "emitY", "url": "http://emitterY:9100" }`. Ensure that the `EMITTER_ID`, `emitY`, matches what you set in the container config and the `url` matches the `emitterY` container name.

---
If you run into dependency issues and would like to manually install, here's how:

To install analyzer dependencies:
- `pip install -r analyzers/requirements.txt`

To install distributor dependencies:
- `pip install -r distributor/requirements.txt`

To install emitter dependencies:
- `pip install -r emitter/requirements.txt`

To install UI dependencies:
- `cd dashboard; npm install`

To run the UI in dev mode:
- `docker compose up --build`
- `cd dashboard; npm run dev`, you will be able to access the UI on `http://localhost:5173/`

---

## Improvements/Future Work 🧑‍💻

This working demo is in a proof-of-concept stage where the components work. Most importantly, the 
SWRR Distributor working is the core of this project. Even though there have been many more features
both on the backend and the front-end added on top of the minimum requirements, there are certain 
important features that I would like to add on to this if I have the time and resources:

1. Able to add new Analyzers at runtime that were not created at build time. This would require an
entire refactor to the Docker setup because currently, all Emitters and Analyzers need a container
at build time. This is why the Add Analyzer feature does not work.
2. Display all logs since the start. This would probably require placing logs into a database 
somewhere other than on your machine's disk memory so it doesn't blow up the memory.
3. Currently if all Analyzers are paused/shutdown, the Emitters are also paused but their packets
are queued in their local buffers to avoid losing data. But that buffer is only 5000 packets in size
so it would still lose data after it is full. I would refactor this so that the packets don't get 
enqueued if Analyzers are offline.
4. Make the UI look prettier.

This project also doesn't contain an exhaustive testing strategy. Given more time I would like to include
some robust testing at different levels of the project:
- *Backend unit tests:* for weight‑redistribution, checking if SWRR works correctly, Emitter pause/resume logic, 
Emitter rate‐limiting edge‑cases, Analyzer enable/disable logic, Distributor queue edge cases.
- *Integration tests:* to ensure Emitters -> Distributor -> Analyzer communication is robust.
- *Scalability/load tests:* that ramp up to >100k req/s from Emitters, keeping watch on latency, CPU usage,
Distributor and Emitter queue depths. Also testing concurrency robustness with >10k Emitters and Analyzers.
- *Front‑end unit tests:* to ensure React components work and API calls are robust and handle errors.
- *Chaos resiliency:* basically checking if the system can handle random Emitters and Analyzers going offline,
coming back online, network latency, spikes in requests.

(Note that scalability tests may require a refactor to the current architecture, it's not feasible to write >10k
Emitter and Analyzer components in the docker-compose.yml)

---