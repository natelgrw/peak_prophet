from typing import List, Optional
import asyncio

# Handle imports whether this file is imported as part of the package or run directly
try:
    from predictions.askcos_scraper import scrape_askcos
    from predictions.rt_pred.rt_pred import predict_retention_time_from_smiles
    from predictions.lmax_pred.lmax_pred import predict_lambda_max_in_conda_env
except Exception:  # pragma: no cover - fallback for direct execution
    from askcos_scraper import scrape_askcos
    from rt_pred.rt_pred import predict_retention_time_from_smiles
    from lmax_pred.lmax_pred import predict_lambda_max_in_conda_env

class PredictedProduct:
    """Represents a predicted product of a reaction."""
    def __init__(self, smiles: str, probability: float, mol_weight: float, retention_time: Optional[float] = None, lambda_max: Optional[float] = None):
        self.smiles = smiles
        self.probability = probability
        self.mol_weight = mol_weight
        self.retention_time = retention_time
        self.lambda_max = lambda_max

    def set_smiles(self, smiles: str):
        self.smiles = smiles
    
    def get_smiles(self) -> str:
        return self.smiles
    
    def set_probability(self, probability: float):
        self.probability = probability
    
    def get_probability(self) -> float:
        return self.probability
    
    def set_mol_weight(self, mol_weight: float):
        self.mol_weight = mol_weight
    
    def get_mol_weight(self) -> float:
        return self.mol_weight

    def set_retention_time(self, retention_time: float):
        self.retention_time = retention_time
    
    def get_retention_time(self) -> float:
        return self.retention_time

    def set_lambda_max(self, lambda_max: float):
        self.lambda_max = lambda_max

    def get_lambda_max(self) -> float:
        return self.lambda_max

    def __repr__(self):
        return f"PredictedProduct(smiles='{self.smiles}', RT={self.retention_time}, λmax={self.lambda_max})"


class ChemicalReaction:
    """Stores a chemical reaction, its conditions, and predicted products."""
    def __init__(self, reactants: List[str], solvents: str):
        self.reactants = reactants
        self.solvents = solvents
        self.products = []
    
    def set_reactants(self, reactants: List[str]):
        self.reactants = reactants
    
    def get_reactants(self) -> List[str]:
        return self.reactants
    
    def set_solvents(self, solvents: str):
        self.solvents = solvents
    
    def get_solvents(self) -> str:
        return self.solvents
    
    def add_product(self, product: PredictedProduct):
        self.products.append(product)
    
    def get_products(self) -> List[PredictedProduct]:
        return self.products

    async def fetch_products_from_askcos(self) -> List[PredictedProduct]:
        """Call ASKCOS scraper to predict products and populate self.products.

        Returns the list of added products.
        """
        results = await scrape_askcos(self.reactants, self.solvents)
        self.products = []
        for item in results:
            try:
                smiles = item["smiles"]
                mol_weight = float(item["mol_weight"]) if item["mol_weight"] is not None else None
                probability = float(item["probability"]) if item["probability"] is not None else None
            except (KeyError, ValueError):
                continue
            self.add_product(PredictedProduct(smiles=smiles, probability=probability, mol_weight=mol_weight))
        return self.products

    def fetch_products_from_askcos_sync(self) -> List[PredictedProduct]:
        """Synchronous wrapper for fetch_products_from_askcos.

        Uses asyncio.run if no running loop is present; otherwise raises RuntimeError
        to avoid interfering with an existing event loop.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.fetch_products_from_askcos())
        raise RuntimeError("fetch_products_from_askcos_sync() cannot run inside an existing event loop. Use the async method instead.")

    async def predict_products_retention_times(self) -> List[PredictedProduct]:
        """Predict retention times for current products and set them in-place.

        Returns the updated list of products.
        """
        if not self.products:
            return self.products
        smiles_list = [p.get_smiles() for p in self.products]
        try:
            results = await predict_retention_time_from_smiles(smiles_list)
        except Exception:
            # If prediction fails, leave retention times as-is
            return self.products
        for idx, product in enumerate(self.products):
            try:
                result = results[idx]
                rt_value = result.get("retention_time")
                rt_float = float(rt_value) if rt_value not in (None, "") else None
                product.set_retention_time(rt_float)
            except Exception:
                continue
        return self.products

    def predict_products_retention_times_sync(self) -> List[PredictedProduct]:
        """Synchronous wrapper for predict_products_retention_times.

        Uses asyncio.run if no running loop is present; otherwise raises RuntimeError
        to avoid interfering with an existing event loop.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.predict_products_retention_times())
        raise RuntimeError("predict_products_retention_times_sync() cannot run inside an existing event loop. Use the async method instead.")

    def predict_products_lambda_max(self, conda_env: str = "uvvismlenv") -> List[PredictedProduct]:
        """Predict lambda max for current products (uses conda env via `conda run`).

        Builds a list of (smiles, solvent) tuples and invokes the chemprop-based
        predictor in the specified conda environment, then sets lambda_max on
        each product when available.
        """
        if not self.products:
            return self.products
        tuples = [(p.get_smiles(), self.get_solvents()) for p in self.products]
        predictions = predict_lambda_max_in_conda_env(tuples, conda_env=conda_env)
        for product in self.products:
            key = (product.get_smiles(), self.get_solvents())
            if key in predictions:
                try:
                    lm = predictions[key]
                    lm_float = float(lm) if lm is not None and lm != "" else None
                    product.set_lambda_max(lm_float)
                except Exception:
                    continue
        return self.products

    def __repr__(self):
        return (f"ChemicalReaction(reactants='{self.reactants}', solvents='{self.solvents}', "
                f"products={self.products})")