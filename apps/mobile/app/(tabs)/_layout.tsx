import { Tabs } from "expo-router";

import { AppIcon } from "../../src/components/AppIcon";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#3E73FF",
        tabBarInactiveTintColor: "#5F6575",
        tabBarHideOnKeyboard: true,
        tabBarItemStyle: {
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "700",
          marginBottom: 6,
        },
        tabBarStyle: {
          borderTopColor: "#DCE4F3",
          borderTopWidth: 1,
          height: 78,
          paddingTop: 6,
        },
      }}
    >
      <Tabs.Screen
        name="projects"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <AppIcon
              background={focused ? "#E8F0FF" : "transparent"}
              color={color}
              name="projects"
              size={24}
            />
          ),
          title: "Projects",
        }}
      />
      <Tabs.Screen
        name="chats"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <AppIcon
              background={focused ? "#EEF0FF" : "transparent"}
              color={color}
              name="chats"
              size={24}
            />
          ),
          title: "Chats",
        }}
      />
      <Tabs.Screen
        name="offline"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <AppIcon
              background={focused ? "#EEF6FF" : "transparent"}
              color={color}
              name="offline"
              size={24}
            />
          ),
          title: "Offline",
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <AppIcon
              background={focused ? "#FFF0E8" : "transparent"}
              color={color}
              name="alerts"
              size={24}
            />
          ),
          title: "Alerts",
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <AppIcon
              background={focused ? "#F1F3FA" : "transparent"}
              color={color}
              name="settings"
              size={24}
            />
          ),
          title: "Settings",
        }}
      />
      <Tabs.Screen name="fcc" options={{ href: null }} />
      <Tabs.Screen name="dt-checkin" options={{ href: null }} />
      <Tabs.Screen name="dt-checkin-new" options={{ href: null }} />
      <Tabs.Screen name="dt-checkin-detail" options={{ href: null }} />
      <Tabs.Screen name="dt-expenses" options={{ href: null }} />
      <Tabs.Screen name="mileage-tracker" options={{ href: null }} />
    </Tabs>
  );
}
