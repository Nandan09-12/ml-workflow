import Svg, { Circle, Path, Rect } from "react-native-svg";

type AppIconName =
  | "alerts"
  | "chats"
  | "checkin"
  | "expenses"
  | "mileage"
  | "offline"
  | "projects"
  | "settings";

type AppIconProps = {
  background?: string;
  color?: string;
  name: AppIconName;
  size?: number;
};

export function AppIcon({
  background = "transparent",
  color = "#2F3565",
  name,
  size = 24,
}: AppIconProps) {
  const strokeWidth = 1.8;
  const icon = renderIcon(name, color, strokeWidth);

  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      {background !== "transparent" ? <Rect fill={background} height="24" rx="7" width="24" x="0" y="0" /> : null}
      {icon}
    </Svg>
  );
}

function renderIcon(name: AppIconName, color: string, strokeWidth: number) {
  switch (name) {
    case "projects":
      return (
        <>
          <Path
            d="M4.5 10.2L12 4.8l7.5 5.4"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Path
            d="M6.5 9.8v8.2h11V9.8"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Path
            d="M10 18v-4.2h4V18"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
        </>
      );
    case "chats":
      return (
        <>
          <Rect
            fill="none"
            height="12"
            rx="3"
            stroke={color}
            strokeWidth={strokeWidth}
            width="16"
            x="4"
            y="5"
          />
          <Path
            d="M8 17l-2.7 2v-2"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Path d="M8 10.1h8M8 13.1h5.5" fill="none" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
        </>
      );
    case "offline":
      return (
        <>
          <Path
            d="M7 6.5h10M7.5 10h9M9.5 13.5h5"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeWidth={strokeWidth}
          />
          <Path
            d="M12 16v4M9.8 18.2L12 20.5l2.2-2.3"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
        </>
      );
    case "alerts":
      return (
        <>
          <Path
            d="M12 5.2a3.3 3.3 0 00-3.3 3.3v1.2c0 .9-.3 1.8-.9 2.5L6.5 14h11l-1.3-1.8a4.3 4.3 0 01-.9-2.5V8.5A3.3 3.3 0 0012 5.2z"
            fill="none"
            stroke={color}
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Path
            d="M10 17.2a2.3 2.3 0 004 0"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeWidth={strokeWidth}
          />
        </>
      );
    case "settings":
      return (
        <>
          <Circle cx="12" cy="12" fill="none" r="3.1" stroke={color} strokeWidth={strokeWidth} />
          <Path
            d="M12 4.6v2.1M12 17.3v2.1M19.4 12h-2.1M6.7 12H4.6M17.2 6.8l-1.5 1.5M8.3 15.7l-1.5 1.5M17.2 17.2l-1.5-1.5M8.3 8.3L6.8 6.8"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeWidth={strokeWidth}
          />
        </>
      );
    case "checkin":
      return (
        <>
          <Rect
            fill="none"
            height="14"
            rx="2.5"
            stroke={color}
            strokeWidth={strokeWidth}
            width="12"
            x="6"
            y="6"
          />
          <Path d="M9 4.8h6" fill="none" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
          <Path
            d="M9.2 12.3l1.7 1.7 3.8-4"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
        </>
      );
    case "expenses":
      return (
        <>
          <Path
            d="M7 5.5h10v13l-2-1.3-2 1.3-2-1.3-2 1.3-2-1.3z"
            fill="none"
            stroke={color}
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Path d="M9.2 9.2h5.6M9.2 12.1h5.6M9.2 15h3.2" fill="none" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
        </>
      );
    case "mileage":
      return (
        <>
          <Path
            d="M7.2 15.8h9.6l-1-4.3a2.2 2.2 0 00-2.1-1.7h-3.4a2.2 2.2 0 00-2.1 1.7z"
            fill="none"
            stroke={color}
            strokeLinejoin="round"
            strokeWidth={strokeWidth}
          />
          <Circle cx="9" cy="16.5" fill="none" r="1.6" stroke={color} strokeWidth={strokeWidth} />
          <Circle cx="15" cy="16.5" fill="none" r="1.6" stroke={color} strokeWidth={strokeWidth} />
          <Path d="M9 8.4l1.2-2.1h3.6L15 8.4" fill="none" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
        </>
      );
    default:
      return null;
  }
}
