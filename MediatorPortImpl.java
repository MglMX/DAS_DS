package org.komparator.mediator.ws;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import javax.jws.HandlerChain;
import javax.jws.WebService;

import org.komparator.mediator.ws.cli.MediatorClient;
import org.komparator.mediator.ws.cli.MediatorClientException;
import org.komparator.supplier.ws.BadProductId_Exception;
import org.komparator.supplier.ws.BadQuantity_Exception;
import org.komparator.supplier.ws.BadText_Exception;
import org.komparator.supplier.ws.InsufficientQuantity_Exception;
import org.komparator.supplier.ws.ProductView;
import org.komparator.supplier.ws.cli.SupplierClient;
import org.komparator.supplier.ws.cli.SupplierClientException;

import com.sun.xml.ws.client.ClientTransportException;

import pt.ulisboa.tecnico.sdis.ws.cli.CreditCardClient;
import pt.ulisboa.tecnico.sdis.ws.cli.CreditCardClientException;

//annotate to bind with WSDL
@WebService(endpointInterface = "org.komparator.mediator.ws.MediatorPortType")

@HandlerChain(file = "/mediator-ws_handler-chain.xml")
public class MediatorPortImpl implements MediatorPortType {

	protected static LocalDateTime mightBeAlive = LocalDateTime.now();
	// end point manager
	private MediatorEndpointManager endpointManager;
	private List<ShoppingResultView> history = new ArrayList<ShoppingResultView>();

	public MediatorPortImpl(MediatorEndpointManager endpointManager) {
		this.endpointManager = endpointManager;
	}

	private Map<String, CartView> carts = new ConcurrentHashMap<>();

	// Main operations -------------------------------------------------------

	@Override
	public List<ItemView> getItems(String id) throws InvalidItemId_Exception {
		if (badString(id))
			throwInvalidItemId("Item ID must not be empty");

		SupplierClient client = null;
		ProductView productV = null;
		List<ItemView> list = new ArrayList<ItemView>();

		List<String> endpointAddresses = connect("A21_Supplier%");

		for (int i = 0; i < endpointAddresses.size(); i++) {
			try {
				client = new SupplierClient(endpointAddresses.get(i));
			} catch (SupplierClientException e) {
				System.out.println("Caught exception when creating the SupplierClient");
			}
			try {
				productV = client.getProduct(id);
			} catch (BadProductId_Exception e) {
				System.out.println("Caught exception while getting product from client");
			}

			if (productV != null) {
				ItemView itemV = translateViews(productV, "A21_Supplier" + endpointAddresses.get(i).charAt(20));
				list.add(itemV);
			}
		}
		list.sort(Comparator.comparing(ItemView::getPrice));

		return list;
	}

	@Override
	public List<ItemView> searchItems(String searchText) throws InvalidText_Exception {
		List<String> supplierAddresses = connect("A21_Supplier%");
		List<ItemView> list = new ArrayList<ItemView>();
		SupplierClient client = null;

		if (badString(searchText)) {
			throwInvalidText("The searchText must not be empty.");
		}

		for (int i = 0; i < supplierAddresses.size(); i++) {
			try {
				client = new SupplierClient(supplierAddresses.get(i));

				List<ProductView> productList = client.searchProducts(searchText);

				for (int j = 0; j < productList.size(); j++) {
					ItemView item = translateViews(productList.get(j),
							"A21_Supplier" + supplierAddresses.get(i).charAt(20));
					list.add(item);
				}

			} catch (SupplierClientException e) {
				System.out.println("Caught exception when creating the SupplierClient");

			} catch (BadText_Exception e) {
				System.out.println("Bad text in Product.");
			}
		}

		Comparator<ItemView> lexicAndPriceComparison = new Comparator<ItemView>() {
			@Override
			public int compare(ItemView item1, ItemView item2) {
				int stringResult = item1.getItemId().getProductId().compareTo(item2.getItemId().getProductId());
				if (stringResult == 0) {
					return item1.getPrice() - item2.getPrice();
				} else {
					return stringResult;
				}
			}
		};

		Collections.sort(list, lexicAndPriceComparison);

		return list;
	}

	public void checkBuyCartArgs(String name, String creditCard)
			throws InvalidCartId_Exception, InvalidCreditCard_Exception {
		if (name == null || name.trim().equals(""))
			throwInvalidCartId("Cart ID is null or invalid");
		if (creditCard == null || creditCard.trim().equals(""))
			throwInvalidCreditCard("Credit card is null or invalid");

	}

	@Override
	public ShoppingResultView buyCart(String name, String creditCard)
			throws EmptyCart_Exception, InvalidCartId_Exception, InvalidCreditCard_Exception {
		checkBuyCartArgs(name, creditCard);

		String ccAddress = "http://ws.sd.rnl.tecnico.ulisboa.pt:8080/cc";

		/*
		 * try { ccAddress =
		 * endpointManager.getUddiNaming().lookup("CreditCard"); } catch
		 * (Exception e) {
		 * 
		 * }
		 * 
		 * if (ccAddress == null) {
		 * System.out.println("No credit card service running!"); return null; }
		 */ // Credit card is not registed in uddi! impossible to do this

		ShoppingResultView result = new ShoppingResultView();

		boolean boughtItem = false;
		boolean droppedItem = false;
		int totalPrice = 0;

		CreditCardClient ccc;
		CartView cart = null;
		List<CartItemView> purchasedItems = result.getPurchasedItems();
		List<CartItemView> droppedItems = result.getDroppedItems();

		try {
			ccc = new CreditCardClient(ccAddress);
		} catch (CreditCardClientException e) {
			return null; // Couldn't create credit card client
		}

		cart = carts.get(name);
		if (cart == null) {
			throwInvalidCartId("No such cart");
		}

		if (!ccc.validateNumber(creditCard)) {
			throwInvalidCreditCard("Credit Card is not valid!");
		}

		// iterate purchases. for each purchase:
		List<CartItemView> items = cart.getItems();

		if (items == null || items.size() == 0)
			throwEmptyCart("Cart is empty");

		for (CartItemView item : items) {
			try {
				// SupplierClient client = new
				// SupplierClient(item.getItem().getItemId().getSupplierId());
				List<String> endpointAddresses = connect(item.getItem().getItemId().getSupplierId());
				SupplierClient client = new SupplierClient(endpointAddresses.get(0));
				client.buyProduct(item.getItem().getItemId().getProductId(), item.getQuantity());
				purchasedItems.add(item); // add to purchased items
				totalPrice += item.getQuantity() * item.getItem().getPrice();
				boughtItem = true;
			} catch (SupplierClientException | InsufficientQuantity_Exception | BadQuantity_Exception
					| BadProductId_Exception e) {
				droppedItems.add(item);
				droppedItem = true;
			}

		}
		if (boughtItem && !droppedItem)
			result.setResult(Result.COMPLETE);
		else if (boughtItem && droppedItem)
			result.setResult(Result.PARTIAL);
		else if (!boughtItem && droppedItem)
			result.setResult(Result.EMPTY);
		else
			throwEmptyCart("Cart is empty"); // Shouldn't happen!

		result.setTotalPrice(totalPrice);
		synchronized (history) {
			history.add(result);

		}
		MediatorClient mc;
		try {
			mc = new MediatorClient("http://localhost:8072/mediator-ws/endpoint");
			mc.updateShopHistory(result);
			mc.updateCart(cart, new Boolean(false));
			System.out.println("Information about history and carts was updated on secondary mediator");

		} catch (MediatorClientException e) {
			System.out.println("Could not update history and carts of 2nd mediator");
			// e.printStackTrace();
		} catch (ClientTransportException e) {
			// Secondary mediator does not exist.
			System.out.println("I dont have a secondary mediator.");// FIXME
		}

		carts.get(name).getItems().clear(); // Remove items from cart

		result.setId(name);

		return result;

	}

	@Override
	public void addToCart(String name, ItemIdView itemView, int quantity) throws InvalidCartId_Exception,
			InvalidItemId_Exception, InvalidQuantity_Exception, NotEnoughItems_Exception {
		if (badString(name))
			throwInvalidCartId("The Cart name must not be empty");
		if (itemView == null || badString(itemView.getProductId()) || badString(itemView.getSupplierId()))
			throwInvalidItemId("ItemIdView is invalid");
		if (quantity <= 0)
			throwInvalidQuantity("quantity must be at least 1");

		ProductView product = null;
		try {
			List<String> endpointAddresses = connect(itemView.getSupplierId());
			SupplierClient client = new SupplierClient(endpointAddresses.get(0));

			product = client.getProduct(itemView.getProductId());

			if (quantity > product.getQuantity())
				throwNotEnoughItems("Not enough Items for the quantity requested");
		} catch (SupplierClientException e) {
			System.out.println("Caught exception when creating the SupplierClient");
		} catch (BadProductId_Exception e) {
			throwInvalidItemId("ItemIdView is invalid");
		} catch (NullPointerException e) {
			throwInvalidItemId("ItemIdView is invalid");
		}

		CartView cartV = carts.get(name);
		if (cartV == null) {
			CartItemView cartItemV = makeCartItemView(itemView, quantity);

			cartV = new CartView();
			cartV.setCartId(name);
			List<CartItemView> list = cartV.getItems();
			list.add(cartItemV);

			carts.put(name, cartV);
		} else {
			boolean newItem = true;
			for (CartItemView c : cartV.getItems()) {
				if (c.getItem().getItemId().getProductId().equals(itemView.getProductId())) {
					if (c.getItem().getItemId().getSupplierId().equals(itemView.getSupplierId())) {
						if (quantity > (product.getQuantity() - c.getQuantity()))
							throwNotEnoughItems("Not enougth Items for the quantity requested");
						c.setQuantity(c.getQuantity() + quantity);
						newItem = false;
					}
				}
			}
			if (newItem) {
				CartItemView cartItemV = makeCartItemView(itemView, quantity);

				cartV.getItems().add(cartItemV); // lista de CartItemViews

			}

		}

		MediatorClient mc;
		try {
			mc = new MediatorClient("http://localhost:8072/mediator-ws/endpoint");
			mc.updateCart(cartV, true);
			System.out.println("Information about carts was updated on secondary mediator");
		} catch (MediatorClientException e) {
			System.out.println("Could not update carts of second mediator");
			// e.printStackTrace();
		} catch (ClientTransportException e) {
			// Secondary mediator does not exist.
			System.out.println("I dont have a secondary mediator.");// FIXME
		}

	}

	// Auxiliary operations --------------------------------------------------
	@Override
	public synchronized List<ShoppingResultView> shopHistory() {
		return history;
	}

	@Override
	public List<CartView> listCarts() {
		List<CartView> result = new ArrayList<CartView>();
		for (Map.Entry<String, CartView> cart : carts.entrySet())
			result.add(cart.getValue());
		return result;
	}

	@Override
	public synchronized void clear() {
		carts.clear();
		history.clear();

		if (endpointManager.getI() == '1'){
			List<String> stateAddresses = connect("A21_Supplier%");
			SupplierClient client = null;
	
			for (String address : stateAddresses) {
				try {
					client = new SupplierClient(address);
	
					client.clear();
				} catch (SupplierClientException e) {
					System.out.println("Caught exception when creating the SupplierClient");
				}
			}
		
			MediatorClient mc;
			try {
				mc = new MediatorClient("http://localhost:8072/mediator-ws/endpoint");
				mc.clear();
				System.out.println("Information about history and carts was cleared on secondary mediator");
			} catch (MediatorClientException e) {
				System.out.println("Could not update carts of second mediator");
				// e.printStackTrace();
			} catch (ClientTransportException e) {
				// Secondary mediator does not exist.
				System.out.println("I dont have a secondary mediator.");// FIXME
			}
		}
		

	}

	public boolean badString(String arg) {
		// check empty string and null
		if (arg == null)
			return true;
		arg = arg.trim();
		if (arg.length() == 0)
			return true;
		return false;

	}

	public List<String> connect(String name) {

		List<String> endpointAddresses = null;

		try {
			endpointAddresses = (List<String>) endpointManager.getUddiNaming().list(name);
		} catch (Exception e) {
			System.out.println("An Error occurred during the connection establishement");
		}

		if (endpointAddresses == null || endpointAddresses.size() == 0) {
			System.out.println("No Addresses found!");
			return null;
		} else {
			return endpointAddresses;
		}
	}

	@Override
	public String ping(String name) {
		List<String> endpointAddresses = null;
		String pingResult = "";
		SupplierClient client = null;

		endpointAddresses = connect("A21_Supplier%");

		for (int i = 0; i < endpointAddresses.size(); i++) {
			System.out.println("Creating stub ...");
			try {
				client = new SupplierClient(endpointAddresses.get(i));
			} catch (SupplierClientException e) {
				System.out.println("Caught exception when creating the SupplierClient");
			}

			pingResult += client.ping(name + String.valueOf(i));
		}
		return pingResult;

	}

	public CartItemView makeCartItemView(ItemIdView itemView, int quantity) throws InvalidItemId_Exception {
		ItemView itemV = new ItemView();
		itemV.setItemId(itemView);
		List<ItemView> l = getItems(itemView.getProductId());
		for (ItemView i : l) {
			if (i.getItemId().getSupplierId().equals(itemView.getSupplierId())) {
				itemV.setDesc(i.getDesc());
				itemV.setPrice(i.getPrice());
				continue;
			}
		}

		CartItemView cartItemV = new CartItemView();
		cartItemV.setItem(itemV);
		cartItemV.setQuantity(quantity);

		return cartItemV;
	}

	// View helpers -----------------------------------------------------

	public ItemView translateViews(ProductView productV, String s) {
		ItemIdView itemIdV = new ItemIdView();
		itemIdV.setProductId(productV.getId());
		itemIdV.setSupplierId(s);

		ItemView itemV = new ItemView();
		itemV.setItemId(itemIdV);
		itemV.setDesc(productV.getDesc());
		itemV.setPrice(productV.getPrice());

		return itemV;
	}

	// Exception helpers -----------------------------------------------------

	private void throwInvalidText(final String message) throws InvalidText_Exception {
		InvalidText faultInfo = new InvalidText();
		faultInfo.message = message;
		throw new InvalidText_Exception(message, faultInfo);
	}

	private void throwInvalidItemId(final String message) throws InvalidItemId_Exception {
		InvalidItemId faultInfo = new InvalidItemId();
		faultInfo.message = message;
		throw new InvalidItemId_Exception(message, faultInfo);
	}

	private void throwInvalidCreditCard(final String message) throws InvalidCreditCard_Exception {
		InvalidCreditCard faultInfo = new InvalidCreditCard();
		faultInfo.message = message;
		throw new InvalidCreditCard_Exception(message, faultInfo);
	}

	private void throwInvalidCartId(final String message) throws InvalidCartId_Exception {
		InvalidCartId faultInfo = new InvalidCartId();
		faultInfo.message = message;
		throw new InvalidCartId_Exception(message, faultInfo);
	}

	private void throwEmptyCart(final String message) throws EmptyCart_Exception {
		EmptyCart faultInfo = new EmptyCart();
		faultInfo.message = message;
		throw new EmptyCart_Exception(message, faultInfo);
	}

	private void throwInvalidQuantity(final String message) throws InvalidQuantity_Exception {
		InvalidQuantity faultInfo = new InvalidQuantity();
		faultInfo.message = message;
		throw new InvalidQuantity_Exception(message, faultInfo);
	}

	private void throwNotEnoughItems(final String message) throws NotEnoughItems_Exception {
		NotEnoughItems faultInfo = new NotEnoughItems();
		faultInfo.message = message;
		throw new NotEnoughItems_Exception(message, faultInfo);
	}

	@Override
	public void updateShopHistory(ShoppingResultView history) {
		char isPrimary = endpointManager.getI();

		if (isPrimary == '1') {
			return;
		} else {
			System.out.println("Received updated history info from primary mediator");
			this.history.add(history);
		}

	}

	@Override
	public void updateCart(CartView cart, Boolean add) {
		char isPrimary = endpointManager.getI();

		if (isPrimary == '1') {
			return;
		} else {
			System.out.println("Received updated cart info from primary mediator");
			if (add.booleanValue()) {
				if (carts.containsKey(cart.getCartId()))
					this.carts.replace(cart.getCartId(), cart);
				else
					this.carts.put(cart.getCartId(), cart);
			} else {
				this.carts.get(cart.getCartId()).getItems().clear();
			}

		}

	}

	@Override
	public void imAlive() {
		char isPrimary = endpointManager.getI();

		if (isPrimary == '1') {
			return;
		} else {
			System.out.println("Received life proof from primary mediator");
			MediatorPortImpl.mightBeAlive = LocalDateTime.now();
		}

	}

}
