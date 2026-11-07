# Deploy WorldFork replay

The deployable service lets judges open the recorded comparison, browse 30 pilot episodes, inspect decisions and download complete traces. It uses the same React frontend as live mode and verifies the bundled evidence before serving requests. Replay needs no model, gateway, GPU, API key or persistent volume.

## Build and verify

```sh
docker build --target checks .
docker build -t worldfork-replay:local .
docker run -d --name worldfork-replay --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:8001:8001 worldfork-replay:local
```

The image runs as an unprivileged user. The temporary filesystem holds a fresh SQLite import of the verified pilot. If port 8001 is occupied, map a different host port such as `-p 127.0.0.1:8004:8001` and use it in the URLs below.

```sh
docker logs worldfork-replay
python3 scripts/check_replay_deployment.py http://127.0.0.1:8001
```

Open [the local replay](http://127.0.0.1:8001). The check verifies readiness, every run identity, the default comparison, decoded export equality and rejection of live write requests. The same build and HTTP checks run in the repository's GitHub Actions workflow after it is pushed to GitHub.

## Host, monitor and roll back

Use the same image and commands on a container host. Route HTTPS to port 8001 through the host's ingress or reverse proxy. For a proxy running on the same machine, keep the loopback port mapping above. Use `/api/health` for readiness and container logs for startup errors and HTTP access logs. Re-run the deployment check against the HTTPS URL before sharing it. Keep the previous image tag to roll back by replacing the replay container. Restarting reconstructs the database from the immutable image contents.

The live evaluation stack uses Ollama on the Mac and sends measured calls through Bifrost. Run the live API on loopback with a single worker and a private SQLite database. Its host and origin checks are browser safeguards for local use. Public access to live inference would require authentication, authorization and resource limits. Use the read-only replay container for sharing recorded evidence.

```sh
python3 scripts/check_replay_deployment.py http://127.0.0.1:8001 \
  --samples-per-route 25 --concurrency 8 --archive-summary
docker stats --no-stream worldfork-replay
```

The workload covers the archive, run detail, event feed and trace export. The reported wire body excludes HTTP headers. The benchmark uses fresh connections and requests gzip. It measures the replay service separately from the agent pilot.
