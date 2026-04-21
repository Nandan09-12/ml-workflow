import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { ProjectIcon } from "./ProjectIcon";
import { projectOptions } from "../data/projects";
import { spacing } from "../theme/tokens";

const projectGlyphs: Record<string, string> = {
  checkin: "✓",
  feedback: "♥",
  inventory: "○",
  vendor: "○",
};

export function ProjectGrid() {
  return (
    <View style={styles.grid}>
      {projectOptions.map((project) => (
        <Pressable
          key={project.id}
          onPress={() => {
            if (project.id === "fcc") {
              router.push("/(tabs)/fcc");
            }
          }}
          style={({ pressed }) => [styles.tile, pressed && project.id === "fcc" && styles.pressed]}
        >
          <ProjectIcon color={project.accentColor} label={projectGlyphs[project.iconKey]} />
          <Text style={styles.tileTitle}>{project.title}</Text>
          {project.subtitle ? <Text style={styles.tileSubtitle}>{project.subtitle}</Text> : null}
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.lg,
    justifyContent: "space-between",
    marginTop: spacing.lg,
  },
  tile: {
    alignItems: "center",
    borderRadius: 16,
    paddingVertical: 8,
    width: "42%",
  },
  pressed: {
    opacity: 0.82,
  },
  tileTitle: {
    color: "#161616",
    fontSize: 15,
    fontWeight: "500",
    marginTop: spacing.sm,
    textAlign: "center",
  },
  tileSubtitle: {
    color: "#161616",
    fontSize: 15,
    fontWeight: "500",
    textAlign: "center",
  },
});
