import { useEffect, useState } from "react";
import type { IProduct } from "./types/product";
import { getProducts } from "./services/product";

const App = () => {

  const [products, setProducts] = useState<IProduct[]>([]);

  useEffect(() => {
    const fetchProducts = async () => {
      const result = await getProducts();
      setProducts(result)
    }
    fetchProducts();
  }, [])

  return (
    <main>
      {products.map((products) => (
        <div key={products.id}>
          <h2>{products.name}</h2>
          <p>Rp {products.price}</p>
        </div>
      ))}
    </main>
  )
}

export default App;