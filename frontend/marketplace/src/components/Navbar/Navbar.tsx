import logo from "../../assets/logo.png";
import styles from "./Navbar.module.css";
import { Link } from "react-router-dom";
import { Search, ShoppingCart,User } from "lucide-react";

const Navbar = () => {
    return (
        <nav className={styles.container}>
            <div className={styles.navLogo}>
                <div className={styles.title}>
                    <h1>Techora</h1>
                    <p>Electronics</p>
                </div>

                <div className={styles.logo}>
                    <img src={logo} alt="Techora" />
                </div>
            </div>

            <div className={styles.menu}>
                <div className={styles.navLinks}>
                        <Link to="/">Home</Link>
                        <Link to="/shop">Shop</Link>
                        <Link to="/brands">Brands</Link>
                        <Link to="/new_arrivals">New Arrivals</Link>
                </div>

                <div className={styles.nav}>
                    <button>
                        <Search />
                    </button>
                    <button>
                        <ShoppingCart />
                    </button>
                    <button>
                        <User />
                    </button>
                </div>
            </div>
        </nav>
    )
}

export default Navbar