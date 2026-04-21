import { Image, StyleSheet } from "react-native";

export function LogoMark() {
  return <Image source={require('../../assets/MLLOGO.png')} style={styles.image} />;
}

const styles = StyleSheet.create({
  image: {
    backgroundColor: 'transparent',
    height: 118,
    resizeMode: 'contain',
    width: 124,
  },
});
