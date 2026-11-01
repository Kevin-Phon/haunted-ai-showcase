import { useEffect, useRef, useState } from "react";

export function AmbientAudio({ src }: { src: string }) {
  const ref = useRef<HTMLAudioElement>(null);
  const [blocked, setBlocked] = useState(false);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    element.volume = 0.2;
    void element.play()?.catch(() => setBlocked(true));
    return () => element.pause();
  }, [src]);
  return (
    <section className="audio-player" aria-label="Ambient sound controls">
      <audio
        ref={ref}
        src={src}
        loop
        controls
        preload="none"
        aria-label="Manor ambience"
        onError={() => setBlocked(true)}
        onPlay={() => setBlocked(false)}
      />
      {blocked && (
        <p>
          Sound could not start. Use Play to try again, or leave sound off. All
          story cues remain visible.
        </p>
      )}
    </section>
  );
}

export function DiscoverySound({
  earned,
  src,
}: {
  earned: number;
  src: string;
}) {
  const ref = useRef<HTMLAudioElement>(null);
  const previous = useRef(earned);
  useEffect(() => {
    const element = ref.current;
    if (earned > previous.current && element) {
      element.volume = 0.25;
      element.currentTime = 0;
      void element.play()?.catch(() => {
        /* Visible progress remains authoritative. */
      });
    }
    previous.current = earned;
  }, [earned]);
  useEffect(() => {
    const element = ref.current;
    return () => element?.pause();
  }, []);
  return <audio ref={ref} src={src} preload="none" />;
}
