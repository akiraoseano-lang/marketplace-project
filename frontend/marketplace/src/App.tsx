import { useEffect, useState } from "react";
import type { IProduct } from "./types/product";
import { getProducts } from "./services/product";
import Navbar from "./components/Navbar";

const App = () => {

  return (
    <main>
      <Navbar />

      <h1>Marketplace</h1>
    </main>
  )
}

export default App;