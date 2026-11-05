"use client";;
import { RTVIEvent } from "@pipecat-ai/client-js";
import {
  usePipecatClientMediaTrack,
  usePipecatClientTransportState,
  useRTVIClientEvent,
} from "@pipecat-ai/client-react";
import { useCallback, useEffect, useReducer, useRef } from "react";

import { DUPLEX_TIMELINE_INITIAL_STATE, reduceDuplexTimeline } from "@/components/pipecat/duplex-timeline-markers";
import {
  createDuplexTimelineRenderer,
  DUPLEX_TIMELINE_HEIGHT,
  DUPLEX_TIMELINE_LANES,
} from "@/components/pipecat/duplex-timeline-renderer";
import { cn } from "@/lib/utils";
import { resolveVisualizerColor } from "@/lib/visualizer";

const DEFAULT_COLORS = {
  agent: "--agent-foreground",
  user: "--client-foreground",
  backchannel: "--muted-foreground",
  interruption: "--inactive-background",
  grid: "--border",
};

/**
 * Label defaults. Segment colors come through the root's custom properties
 * so a label class name can override them.
 */
const LABEL_CLASSES = {
  backchannel:
    "text-[10px] leading-none text-(color:--duplex-timeline-backchannel)",
  interruption:
    "text-[10px] leading-none text-(color:--duplex-timeline-interruption)",
  latency:
    "text-[10px] leading-none data-slow:text-(color:--duplex-timeline-slow-reply)",
  time: "text-[10px] leading-none opacity-50",
};

/** A color prop as CSS: "--token" names become var(--token). */
function cssColor(color) {
  return color.startsWith("--") ? `var(${color})` : color;
}

/**
 * A color prop for the canvas. Tokens resolve on the canvas itself, so an
 * override scoped to the timeline reaches the bars as well as the DOM parts.
 */
function canvasColor(color, canvas) {
  if (!color.startsWith("--")) return resolveVisualizerColor(color, canvas);
  return getComputedStyle(canvas).getPropertyValue(color).trim() || "black";
}

/**
 * Scrolling agent and user waveforms. Handoff rules, latency and time labels
 * use the element's text color. Labels over the canvas are DOM spans.
 */
export function DuplexTimelineView({
  agentTrack = null,
  userTrack = null,
  markers,
  running = false,
  agentSpeaking = false,
  userSpeaking = false,
  agentLabel = "agent",
  userLabel = "you",
  agentColor = DEFAULT_COLORS.agent,
  userColor = DEFAULT_COLORS.user,
  backchannelColor = DEFAULT_COLORS.backchannel,
  interruptionColor = DEFAULT_COLORS.interruption,
  slowReplyColor = interruptionColor,
  gridColor = DEFAULT_COLORS.grid,
  slowReplyMs = 1000,
  noBackchannels = false,
  noInterruptions = false,
  noHandoffs = false,
  noLatency = false,
  noLaneLabels = false,
  noSegmentLabels = false,
  noTimeLabels = false,
  noLegend = false,
  className,
  legendClassName,
  laneLabelClassName,
  backchannelLabelClassName,
  interruptionLabelClassName,
  latencyLabelClassName,
  timeLabelClassName
}) {
  const canvasRef = useRef(null);
  const labelsRef = useRef(null);
  const rendererRef = useRef(null);

  // The renderer owns the frame loop, audio and label spans; props are
  // pushed into it.
  useEffect(() => {
    const canvas = canvasRef.current;
    const labels = labelsRef.current;
    if (!canvas || !labels) return;
    const renderer = createDuplexTimelineRenderer(canvas, labels);
    rendererRef.current = renderer;
    return () => {
      renderer.dispose();
      rendererRef.current = null;
    };
  }, []);

  // Resolve colors now and whenever the theme changes, on <html> or with the
  // OS. className is a dependency because it can change what they resolve to.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const apply = () => {
      rendererRef.current?.setPalette({
        agent: canvasColor(agentColor, canvas),
        user: canvasColor(userColor, canvas),
        backchannel: canvasColor(backchannelColor, canvas),
        interruption: canvasColor(interruptionColor, canvas),
        slowReply: canvasColor(slowReplyColor, canvas),
        grid: canvasColor(gridColor, canvas),
        text: canvasColor("currentColor", canvas),
      });
    };
    apply();
    const observer = new MutationObserver(apply);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "style", "data-theme"],
    });
    const scheme = matchMedia("(prefers-color-scheme: dark)");
    scheme.addEventListener("change", apply);
    return () => {
      observer.disconnect();
      scheme.removeEventListener("change", apply);
    };
  }, [
    agentColor,
    userColor,
    backchannelColor,
    interruptionColor,
    slowReplyColor,
    gridColor,
    className,
  ]);

  // Before markers, so the first frame creates label spans with their classes.
  useEffect(() => {
    rendererRef.current?.setOptions({
      slowReplyMs,
      backchannels: !noBackchannels,
      interruptions: !noInterruptions,
      handoffs: !noHandoffs,
      latency: !noLatency,
      segmentLabels: !noSegmentLabels,
      timeLabels: !noTimeLabels,
      labelClassNames: {
        backchannel: cn(LABEL_CLASSES.backchannel, backchannelLabelClassName),
        interruption: cn(
          LABEL_CLASSES.interruption,
          interruptionLabelClassName,
        ),
        latency: cn(LABEL_CLASSES.latency, latencyLabelClassName),
        time: cn(LABEL_CLASSES.time, timeLabelClassName),
      },
    });
  }, [
    slowReplyMs,
    noBackchannels,
    noInterruptions,
    noHandoffs,
    noLatency,
    noSegmentLabels,
    noTimeLabels,
    backchannelLabelClassName,
    interruptionLabelClassName,
    latencyLabelClassName,
    timeLabelClassName,
  ]);

  useEffect(() => {
    rendererRef.current?.setTrack("agent", agentTrack);
  }, [agentTrack]);

  useEffect(() => {
    rendererRef.current?.setTrack("user", userTrack);
  }, [userTrack]);

  useEffect(() => {
    rendererRef.current?.setMarkers(markers ?? []);
  }, [markers]);

  useEffect(() => {
    const renderer = rendererRef.current;
    if (!renderer) return;
    if (running) renderer.reset();
    renderer.setRunning(running);
  }, [running]);

  const { agent, user } = DUPLEX_TIMELINE_LANES;

  return (
    <div
      data-slot="duplex-timeline"
      data-state={running ? "live" : "idle"}
      className={cn(
        "text-muted-foreground flex flex-col gap-4 font-mono text-[11px]",
        className,
      )}
      style={
        {
          "--duplex-timeline-backchannel": cssColor(backchannelColor),
          "--duplex-timeline-interruption": cssColor(interruptionColor),
          "--duplex-timeline-slow-reply": cssColor(slowReplyColor)
        }
      }
    >
      {!noLegend && (
        <DuplexTimelineLegend
          backchannelColor={backchannelColor}
          interruptionColor={interruptionColor}
          noBackchannels={noBackchannels}
          noInterruptions={noInterruptions}
          noHandoffs={noHandoffs}
          className={legendClassName}
        />
      )}
      <div className="flex gap-3">
        {!noLaneLabels && (
          <div
            className="flex shrink-0 flex-col"
            style={{
              paddingTop: agent.top,
              rowGap: user.top - agent.top - agent.height,
            }}
          >
            <LaneLabel
              lane="agent"
              label={agentLabel}
              color={agentColor}
              speaking={agentSpeaking}
              height={agent.height}
              className={laneLabelClassName}
            />
            <LaneLabel
              lane="user"
              label={userLabel}
              color={userColor}
              speaking={userSpeaking}
              height={user.height}
              className={laneLabelClassName}
            />
          </div>
        )}
        <div className="relative min-w-0 flex-1 [mask-image:linear-gradient(to_right,transparent,black_3rem)]">
          <canvas
            ref={canvasRef}
            role="img"
            aria-label={`${agentLabel} and ${userLabel} speech over time`}
            className="block w-full"
            style={{ height: DUPLEX_TIMELINE_HEIGHT }}
          />
          <div
            ref={labelsRef}
            aria-hidden
            className="pointer-events-none absolute inset-0 overflow-hidden"
          />
        </div>
      </div>
    </div>
  );
}

/** Lane name, lit while that side speaks. */
function LaneLabel({
  lane,
  label,
  color,
  speaking,
  height,
  className
}) {
  return (
    <span
      data-slot="duplex-timeline-lane-label"
      data-lane={lane}
      data-state={speaking ? "speaking" : "silent"}
      className={cn(
        "group/lane data-[state=speaking]:text-foreground flex items-center gap-1.5",
        className,
      )}
      style={{ height }}
    >
      <span
        aria-hidden
        className="size-1.5 shrink-0 rounded-full opacity-35 transition-opacity duration-150 group-data-[state=speaking]/lane:opacity-100 motion-reduce:transition-none"
        style={{ backgroundColor: cssColor(color) }}
      />
      {label}
    </span>
  );
}

/** Key for the colors and rules the lane labels don't explain. */
export function DuplexTimelineLegend({
  backchannelColor = DEFAULT_COLORS.backchannel,
  interruptionColor = DEFAULT_COLORS.interruption,
  noBackchannels = false,
  noInterruptions = false,
  noHandoffs = false,
  className
}) {
  const swatches = [
    { label: "backchannel", color: backchannelColor, hidden: noBackchannels },
    {
      label: "interruption",
      color: interruptionColor,
      hidden: noInterruptions,
    },
  ].filter((swatch) => !swatch.hidden);
  return (
    <span
      data-slot="duplex-timeline-legend"
      className={cn(
        "text-muted-foreground flex items-center gap-3 font-mono text-[11px]",
        className,
      )}
    >
      {swatches.map(({ label, color }) => (
        <span key={label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="h-2 w-1"
            style={{ backgroundColor: cssColor(color) }}
          />
          {label}
        </span>
      ))}
      {!noHandoffs && (
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="h-2 w-px border-l border-dashed border-current"
          />
          handoff
        </span>
      )}
    </span>
  );
}

/** Forwards an RTVI turn event, stamped on arrival, with a stable handler. */
function useTurnEvent(
  event,
  type,
  dispatch,
) {
  const handler = useCallback(
    () => dispatch({ type, now: performance.now() }),
    [dispatch, type],
  );
  useRTVIClientEvent(event, handler);
}

/**
 * Turn markers and speaking state from RTVI turn and backchannel events.
 * Requires PipecatClientProvider and an RTVI 2.2 bot for backchannels.
 */
export function useDuplexTimelineMarkers() {
  const [state, dispatch] = useReducer(
    reduceDuplexTimeline,
    DUPLEX_TIMELINE_INITIAL_STATE,
  );

  useTurnEvent(RTVIEvent.Connected, "connected", dispatch);
  useTurnEvent(RTVIEvent.Disconnected, "disconnected", dispatch);
  useTurnEvent(
    RTVIEvent.UserStartedSpeaking,
    "user-started-speaking",
    dispatch,
  );
  useTurnEvent(
    RTVIEvent.UserStoppedSpeaking,
    "user-stopped-speaking",
    dispatch,
  );
  useTurnEvent(RTVIEvent.BotStartedSpeaking, "bot-started-speaking", dispatch);
  useTurnEvent(RTVIEvent.BotStoppedSpeaking, "bot-stopped-speaking", dispatch);

  const onBotOutput = useCallback((data) => {
    // Only a backchannel's first event carries its text; the rest report
    // how much has been spoken.
    if (data.text_type !== "backchannel") return;
    if (data.spoken_status && data.spoken_status !== "new") return;
    dispatch({
      type: "bot-backchannel",
      text: data.text.trim(),
      now: performance.now(),
    });
  }, []);
  useRTVIClientEvent(RTVIEvent.BotOutput, onBotOutput);

  const onUserInput = useCallback((data) => {
    if (data.input_type !== "backchannel") return;
    dispatch({
      type: "user-backchannel",
      text: data.text.trim(),
      now: performance.now(),
    });
  }, []);
  useRTVIClientEvent(RTVIEvent.UserInput, onUserInput);

  return {
    markers: state.markers,
    agentSpeaking: state.botSpeaking,
    userSpeaking: state.userSpeaking,
  };
}

/** Requires PipecatClientProvider; scrolls while the transport is ready. */
export function DuplexTimeline(props) {
  const agentTrack = usePipecatClientMediaTrack("audio", "bot");
  const userTrack = usePipecatClientMediaTrack("audio", "local");
  const running = usePipecatClientTransportState() === "ready";
  const { markers, agentSpeaking, userSpeaking } = useDuplexTimelineMarkers();

  return (
    <DuplexTimelineView
      {...props}
      agentTrack={agentTrack}
      userTrack={userTrack}
      markers={markers}
      running={running}
      agentSpeaking={agentSpeaking}
      userSpeaking={userSpeaking}
    />
  );
}
