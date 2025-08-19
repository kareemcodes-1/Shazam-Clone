import { useState, useRef} from "react";
import { useFormStatus } from "react-dom";
import toast from "react-hot-toast";
import OrbitProgress from "react-loading-indicators/OrbitProgress";

type Song = {
  title: string,
  album_cover: string,
  artist: string

}

const SubmitButton = () => {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="bg-green-600 hover:bg-green-700 py-3 rounded-lg font-semibold transition-all duration-300 disabled:bg-gray-600"
    >
      {pending ? (
        <OrbitProgress
          variant="track-disc"
          color="white"
          size="small"
          style={{ fontSize: "5px" }}
        />
      ) : (
        "Add Song"
      )}
    </button>
  );
};

const Hero = () => {
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
const [songData, setSongData] = useState<Song | null>(null);
const [, setAudioURL] = useState<string | null>(null);



  const handleSubmit = async (formData: FormData) => {
    const spotifyUrl = formData.get("spotify-url") as string;
    if (!spotifyUrl.trim()) {
      alert("Please enter a Spotify track link.");
      return;
    }

    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/add-song`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spotify_url: spotifyUrl }),
      });

      if (!res.ok) throw new Error("Failed to fetch song data");

      const data = await res.json();
      if(data){
        toast.success(`${data.meta.title} by ${data.meta.artist} was uploaded.`)
      }
    } catch (err) {
      console.error(err);
      alert("Something went wrong.");
    }
  };

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);

    mediaRecorderRef.current.ondataavailable = (event: BlobEvent) => {
      audioChunks.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = async () => {
  const blob = new Blob(audioChunks.current, { type: "audio/wav" });
  audioChunks.current = [];

  // Create a temporary URL for playback
  const url = URL.createObjectURL(blob);
  setAudioURL(url);

  // Send to backend
  const formData = new FormData();
  formData.append("file", blob, "audio.wav");

  const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/audio/recognize`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (data.match) {
    toast.success(`Found ${data.match.title} by ${data.match.artist} as a match`)
    setSongData(data.match);
  }
};

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-4">

      <div className="mb-[2rem]">
        {isRecording ? (
          <div id="atom" onClick={stopRecording} className="cursor-pointer">
            <div id="nucleus" className="text-[4rem] text-white">
              Stop Listening
            </div>
          </div>
        ) : (
          <div id="atom" onClick={startRecording} className="cursor-pointer">
            <div id="nucleus" className="text-[4rem] text-white">
              Listen
            </div>
          </div>
        )}
      </div>

      <div className="w-full max-w-lg bg-gray-900 rounded-xl shadow-xl p-6">
        <h1 className="text-2xl font-bold mb-4 text-center">
          Add Song from Spotify
        </h1>

        <form action={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Enter Spotify track link"
            name="spotify-url"
            className="px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 focus:outline-none focus:border-green-500 text-white"
          />

          <SubmitButton />
        </form>

        {songData && (
          <div className="mt-6 p-4 bg-gray-800 rounded-lg">
            <h2 className="text-lg font-bold mb-2">Song Data:</h2>
            <img src={songData.album_cover} alt={songData.title} className="w-full h-[15rem] object-cover"/>
            <div className="mt-[1rem]">
              <p className="text-[1.2rem]">
              <strong>Title:</strong> {songData.title}
            </p>
            <p className="text-[1.2rem]">
              <strong>Artist:</strong> {songData.artist}
            </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default Hero;
