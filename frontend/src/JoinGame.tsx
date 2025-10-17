import { useParams } from "react-router-dom";
import { useState } from "react";

export default function JoinGame() {
  const { gameId } = useParams();
  const [name, setName] = useState("");

  async function join() {
    const res = await fetch(
      `http://localhost:18081/api/v1/game/${gameId}/join?name=${encodeURIComponent(name)}`,
      { method: "POST" }
    );
    const data = await res.json();
    alert(`Joined game as ${name} (seat ${data.seat})`);
  }

  return (
    <div className="p-4 space-y-4">
      <h1>Join Game</h1>
      <p>Game ID: {gameId}</p>
      <input
        type="text"
        placeholder="Enter your name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="border px-2 py-1"
      />
      <button onClick={join} disabled={!name}>
        Join Game
      </button>
    </div>
  );
}
