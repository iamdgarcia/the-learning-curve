"use client";;
import {
  usePipecatClient,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import {
  Loader2Icon,
  PhoneIcon,
  PhoneOffIcon,
  RefreshCwIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const SPINNER = <Loader2Icon className="animate-spin" />;

// Nova's icon-* sizes render a square button; the view responds by going
// icon-only (no label, no min-width).
function isIconSize(size) {
  return typeof size === "string" && size.startsWith("icon");
}

// Default glyphs for icon-only rendering. Text sizes stay label-first
// (spinner only on transitional states), so these apply only when an
// icon-* size is used and neither the state nor the consumer set an icon.
const DEFAULT_STATE_ICONS = {
  disconnected: <PhoneIcon />,
  initializing: SPINNER,
  initialized: <PhoneIcon />,
  authenticating: SPINNER,
  authenticated: SPINNER,
  connecting: SPINNER,
  connected: <PhoneOffIcon />,
  ready: <PhoneOffIcon />,
  disconnecting: SPINNER,
  error: <RefreshCwIcon />,
};

// Idle states: solid active-token fill — the kit's "go" affordance.
const CONNECT_CLASSES =
  "bg-active text-active-foreground hover:bg-active/85 focus-visible:ring-active/40 focus-visible:border-active";
// Connected states: tinted inactive-token surface — the kit's "stop"
// affordance (nova's destructive-button idiom, as on the screen control).
const DISCONNECT_CLASSES =
  "border-inactive/30 bg-inactive/10 text-inactive hover:bg-inactive/20 hover:text-inactive dark:bg-inactive/20";

const DEFAULT_STATE_PROPS = {
  disconnected: { children: "Connect", className: CONNECT_CLASSES },
  initializing: {
    children: "Initializing…",
    icon: SPINNER,
    variant: "secondary",
    disabled: true,
  },
  initialized: { children: "Connect", className: CONNECT_CLASSES },
  authenticating: {
    children: "Connecting…",
    icon: SPINNER,
    variant: "secondary",
    disabled: true,
  },
  authenticated: {
    children: "Connecting…",
    icon: SPINNER,
    variant: "secondary",
    disabled: true,
  },
  connecting: {
    children: "Connecting…",
    icon: SPINNER,
    variant: "secondary",
    disabled: true,
  },
  connected: {
    children: "Disconnect",
    variant: "outline",
    className: DISCONNECT_CLASSES,
  },
  ready: {
    children: "Disconnect",
    variant: "outline",
    className: DISCONNECT_CLASSES,
  },
  disconnecting: {
    children: "Disconnecting…",
    icon: SPINNER,
    variant: "secondary",
    disabled: true,
  },
  error: { children: "Retry", variant: "destructive" },
};

/** States where the transport is between stable endpoints. */
const TRANSITIONAL_STATES = [
  "initializing",
  "authenticating",
  "authenticated",
  "connecting",
  "disconnecting",
];

/** States where clicking tears the session down rather than starting one. */
const DISCONNECT_STATES = [
  "authenticating",
  "authenticated",
  "connecting",
  "connected",
  "ready",
];

/** State overrides take precedence over component props, then defaults. Icon-only buttons use the label as their accessible name. */
export function ConnectButtonView({
  transportState = "disconnected",
  onConnect,
  onDisconnect,
  onClick,
  children,
  stateProps,
  variant,
  size,
  className,
  disabled,
  ...props
}) {
  const defaults = DEFAULT_STATE_PROPS[transportState];
  const overrides = stateProps?.[transportState] ?? {};
  const iconOnly = isIconSize(size);

  // null is meaningful for content (renders nothing); undefined falls back.
  const resolvedLabel =
    overrides.children !== undefined
      ? overrides.children
      : children !== undefined
        ? children
        : defaults.children;
  const label = iconOnly ? null : resolvedLabel;
  const icon =
    overrides.icon !== undefined
      ? overrides.icon
      : iconOnly
        ? (defaults.icon ?? DEFAULT_STATE_ICONS[transportState])
        : defaults.icon;
  // An explicit variant opts out of the default token styling, which is
  // designed around the state's default variant.
  const stateClassName =
    (overrides.variant ?? variant) ? undefined : defaults.className;

  const handleClick = (event) => {
    onClick?.(event);
    if (overrides.onClick) {
      overrides.onClick(event);
    } else if (DISCONNECT_STATES.includes(transportState)) {
      onDisconnect?.();
    } else {
      onConnect?.();
    }
  };

  return (
    <Button
      data-slot="connect-button"
      data-state={transportState}
      variant={overrides.variant ?? variant ?? defaults.variant}
      size={size}
      disabled={disabled || (overrides.disabled ?? defaults.disabled)}
      aria-busy={TRANSITIONAL_STATES.includes(transportState) || undefined}
      aria-label={
        iconOnly && typeof resolvedLabel === "string"
          ? resolvedLabel
          : undefined
      }
      onClick={handleClick}
      className={cn(
        !iconOnly && "min-w-32",
        stateClassName,
        className,
        overrides.className,
      )}
      {...props}
    >
      {icon}
      {label}
    </Button>
  );
}

/** Requires PipecatClientProvider. Pass onConnect when your app owns bot startup. */
export function ConnectButton({
  onConnect,
  onDisconnect,
  ...props
}) {
  const client = usePipecatClient();
  const transportState = usePipecatClientTransportState();

  const handleConnect = () => {
    if (onConnect) {
      onConnect();
      return;
    }
    try {
      // Connection failures surface through the transport's "error" state.
      client?.connect().catch(() => {});
    } catch {
      // connect() can also throw synchronously (e.g. missing connection
      // params); the client reports it, nothing more to do here.
    }
  };

  const handleDisconnect = () => {
    if (onDisconnect) {
      onDisconnect();
      return;
    }
    client?.disconnect().catch(() => {});
  };

  return (
    <ConnectButtonView
      transportState={transportState}
      onConnect={handleConnect}
      onDisconnect={handleDisconnect}
      {...props}
    />
  );
}
