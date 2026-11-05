import { DUPLEX_TIMELINE_HISTORY_MS } from "@/components/pipecat/duplex-timeline-renderer";

export const DUPLEX_TIMELINE_INITIAL_STATE = {
  markers: [],
  nextId: 0,
  userSpeaking: false,
  botSpeaking: false,
  botReplying: false,
  replyId: null,
  replyEndedAt: null,
  userStoppedAt: null,
  interrupted: false,
};

/** How long a user turn may trail the end of a reply and still have overlapped it. */
const LATE_INTERRUPTION_MS = 1500;

/** Adds a marker, dropping those older than the renderer's level history. */
function withMarker(state, markers, marker) {
  const cutoff = marker.at - DUPLEX_TIMELINE_HISTORY_MS;
  return {
    markers: [
      ...markers.filter((existing) => existing.at >= cutoff),
      { ...marker, id: state.nextId },
    ],
    nextId: state.nextId + 1,
  };
}

/** Ends open bot backchannels and interruptions; the same array if none were open. */
function closeOpen(markers, now) {
  let changed = false;
  const next = markers.map((marker) => {
    if (marker.kind === "bot-backchannel" && marker.end === null) {
      changed = true;
      return { ...marker, end: now };
    }
    if (marker.kind === "interruption" && marker.cutAt === null) {
      changed = true;
      return { ...marker, cutAt: now };
    }
    return marker;
  });
  return changed ? next : markers;
}

/**
 * Turns RTVI turn and backchannel events into timeline markers: handoffs
 * with reply latency, interruptions, and backchannels on either side.
 * User turn events mark turns only; a user backchannel arrives on its own.
 */
export function reduceDuplexTimeline(state, event) {
  const { now } = event;
  switch (event.type) {
    case "connected":
      return { ...DUPLEX_TIMELINE_INITIAL_STATE, nextId: state.nextId };

    case "disconnected":
      return {
        ...state,
        markers: closeOpen(state.markers, now),
        userSpeaking: false,
        botSpeaking: false,
        botReplying: false,
        replyId: null,
        interrupted: false,
      };

    case "user-started-speaking":
      if (state.botReplying) {
        return {
          ...state,
          ...withMarker(state, state.markers, {
            kind: "interruption",
            at: now,
            cutAt: null,
          }),
          interrupted: true,
          userSpeaking: true,
        };
      }
      if (
        state.replyEndedAt !== null &&
        now - state.replyEndedAt < LATE_INTERRUPTION_MS
      ) {
        return {
          ...state,
          ...withMarker(state, state.markers, {
            kind: "possible-interruption",
            at: now,
            cutAt: state.replyEndedAt,
          }),
          replyEndedAt: null,
          userSpeaking: true,
        };
      }
      return { ...state, userSpeaking: true };

    case "user-stopped-speaking":
      return {
        ...state,
        ...withMarker(state, state.markers, { kind: "turn-end", at: now }),
        userSpeaking: false,
        userStoppedAt: now,
      };

    case "bot-started-speaking": {
      // Inside the user's turn it's a backchannel playing.
      if (state.userSpeaking) return { ...state, botSpeaking: true };
      const reply =
        state.userStoppedAt === null
          ? null
          : withMarker(state, state.markers, {
              kind: "reply",
              at: now,
              from: state.userStoppedAt,
            });
      return {
        ...state,
        ...reply,
        botSpeaking: true,
        botReplying: true,
        replyId: reply ? state.nextId : null,
        userStoppedAt: null,
      };
    }

    case "bot-stopped-speaking":
      return {
        ...state,
        markers: closeOpen(state.markers, now),
        botSpeaking: false,
        botReplying: false,
        replyId: null,
        replyEndedAt: state.botReplying && !state.interrupted ? now : null,
        interrupted: false,
      };

    case "bot-backchannel": {
      // Bot output follows bot-started-speaking, so the current speech may
      // have read as a reply: undo that reply and keep the turn pending.
      const reply = state.markers.find(
        (marker) => marker.kind === "reply" && marker.id === state.replyId,
      );
      return {
        ...state,
        ...withMarker(
          state,
          state.markers.filter((marker) => marker !== reply),
          { kind: "bot-backchannel", at: now, end: null, text: event.text },
        ),
        userStoppedAt:
          reply?.kind === "reply" ? reply.from : state.userStoppedAt,
        botReplying: false,
        replyId: null,
      };
    }

    case "user-backchannel":
      return {
        ...state,
        ...withMarker(state, state.markers, {
          kind: "user-backchannel",
          at: now,
          text: event.text,
        }),
      };
  }
}
